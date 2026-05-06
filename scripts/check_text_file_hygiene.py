"""Check tracked public text files for portable line endings and layout."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Iterable, Sequence


BINARY_SUFFIXES = {
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".webp",
    ".whl",
    ".zip",
}

TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mdc",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".txt",
    ".yaml",
    ".yml",
}

CRITICAL_MIN_LINES = {
    "README.md": 80,
    "pyproject.toml": 30,
    ".gitattributes": 10,
    ".editorconfig": 8,
    ".github/workflows/ci.yml": 30,
    ".github/actions/guard/action.yml": 30,
    ".github/actions/guard/README.md": 15,
    ".github/workflows/qa-z-example.yml.example": 15,
    "skills/qa-z-merge-safety/SKILL.md": 40,
    "skills/qa-z-merge-safety/README.md": 20,
    "scripts/check_text_file_hygiene.py": 80,
    "scripts/alpha_release_gate.py": 150,
    "qa-z.yaml.example": 40,
}

COLLAPSE_SUFFIXES = {
    ".md",
    ".mdc",
    ".py",
    ".toml",
    ".yaml",
    ".yml",
}

COMPOUND_TEXT_SUFFIXES = (
    ".toml.example",
    ".yaml.example",
    ".yml.example",
)


@dataclass(frozen=True)
class HygieneIssue:
    """One actionable text hygiene issue."""

    path: str
    reason: str


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail when tracked public text files have broken hygiene."
    )
    parser.add_argument(
        "--path",
        default=".",
        help="repository root to inspect; defaults to the current directory",
    )
    parser.add_argument(
        "--source",
        nargs="+",
        default=["working-tree"],
        metavar="SOURCE",
        help=(
            "byte source to inspect: working-tree, git-head, or git-ref REF; "
            "defaults to working-tree"
        ),
    )
    args = parser.parse_args(argv)
    root = Path(args.path).expanduser().resolve()
    source, ref = parse_source_args(args.source, parser)
    issues = check_repository(root, source, ref)
    if not issues:
        print("text file hygiene passed")
        return 0
    print("text file hygiene failed")
    for issue in issues:
        print(f"- {issue.path}: {issue.reason}")
    return 1


def parse_source_args(
    values: Sequence[str], parser: argparse.ArgumentParser
) -> tuple[str, str | None]:
    """Return a normalized source kind and optional git ref."""
    if not values:
        parser.error("--source requires a value")
    source = values[0]
    if source == "working-tree":
        if len(values) != 1:
            parser.error("--source working-tree does not accept a ref")
        return source, None
    if source == "git-head":
        if len(values) != 1:
            parser.error("--source git-head does not accept a ref")
        return source, "HEAD"
    if source == "git-ref":
        if len(values) != 2:
            parser.error("--source git-ref requires exactly one REF")
        return source, values[1]
    parser.error("--source must be one of: working-tree, git-head, git-ref REF")
    raise AssertionError("argparse parser.error exits")


def check_repository(root: Path, source: str, ref: str | None) -> list[HygieneIssue]:
    """Check tracked files from the requested byte source."""
    if source == "working-tree":
        return check_paths(root, tracked_paths(root))
    if ref is None:
        raise ValueError("git blob sources require a ref")
    return check_git_ref(root, ref)


def tracked_paths(root: Path) -> list[Path]:
    """Return tracked repository paths from git."""
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "git ls-files failed; run this script from a Git checkout "
            "or pass --path to one"
        )
    paths: list[Path] = []
    for raw in completed.stdout.split(b"\0"):
        if raw:
            paths.append(root / raw.decode("utf-8", errors="surrogateescape"))
    return paths


def tracked_blob_paths(root: Path, ref: str) -> list[str]:
    """Return tracked blob paths from a Git tree."""
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-tree", "-r", "-z", "--name-only", ref],
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(f"git ls-tree failed for {ref}: {message}")
    paths: list[str] = []
    for raw in completed.stdout.split(b"\0"):
        if raw:
            paths.append(raw.decode("utf-8", errors="surrogateescape"))
    return paths


def git_blob_bytes(root: Path, ref: str, relative: str) -> bytes:
    """Return raw committed blob bytes for a path at ref."""
    completed = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{relative}"],
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(f"git show failed for {ref}:{relative}: {message}")
    return completed.stdout


def check_git_ref(root: Path, ref: str) -> list[HygieneIssue]:
    """Check all tracked blobs at a Git ref."""
    issues: list[HygieneIssue] = []
    for relative in sorted(tracked_blob_paths(root, ref)):
        data = git_blob_bytes(root, ref, relative)
        issues.extend(check_blob(relative, data))
    return issues


def check_paths(root: Path, paths: Iterable[Path]) -> list[HygieneIssue]:
    """Check a provided path set and return all hygiene issues."""
    issues: list[HygieneIssue] = []
    for path in sorted(paths, key=lambda item: relative_path(root, item)):
        if not path.is_file():
            continue
        relative = relative_path(root, path)
        data = path.read_bytes()
        issues.extend(check_blob(relative, data))
    return issues


def check_blob(relative: str, data: bytes) -> list[HygieneIssue]:
    """Check one path/blob pair and return all hygiene issues for it."""
    if should_skip_binary(relative, data):
        return []
    if b"\0" in data:
        return [HygieneIssue(relative, "contains NUL bytes")]
    if b"\r\n" in data:
        return [HygieneIssue(relative, "contains CRLF line endings")]
    if b"\r" in data:
        return [HygieneIssue(relative, "contains CR-only line endings")]
    collapsed_reason = collapsed_public_file_reason(relative, data)
    if collapsed_reason:
        return [HygieneIssue(relative, collapsed_reason)]
    return []


def should_skip_binary(relative: str | Path, data: bytes) -> bool:
    """Return whether a path should be treated as binary for this check."""
    normalized = normalize_relative(relative)
    suffix = PurePosixPath(normalized).suffix.lower()
    if suffix in BINARY_SUFFIXES:
        return True
    if is_text_path(relative):
        return False
    if b"\0" in data:
        return True
    if looks_binary(data):
        return True
    return False


def looks_binary(data: bytes) -> bool:
    """Return whether unknown-suffix bytes look binary enough to skip."""
    if not data:
        return False
    sample = data[:4096]
    control_bytes = sum(
        1 for byte in sample if byte < 32 and byte not in {8, 9, 10, 12, 13, 27}
    )
    return control_bytes / len(sample) > 0.30


def is_text_path(path: str | Path) -> bool:
    """Return whether a path is expected to be text by name or suffix."""
    normalized = normalize_relative(path).lower()
    pure_path = PurePosixPath(normalized)
    name = pure_path.name
    if name in {".editorconfig", ".gitattributes", ".gitignore"}:
        return True
    if normalized.endswith(COMPOUND_TEXT_SUFFIXES):
        return True
    return pure_path.suffix.lower() in TEXT_SUFFIXES


def collapsed_public_file_reason(relative: str, data: bytes) -> str | None:
    """Return a reason when a critical public file looks line-collapsed."""
    min_lines = min_lines_for_public_file(relative)
    line_count = data.count(b"\n")
    if min_lines is None:
        if generic_collapsed_text_file(relative, data, line_count):
            return (
                f"suspiciously collapsed into {line_count} LF-separated line(s); "
                "public Markdown/YAML/TOML/Python files must be readable multiline text"
            )
        return None
    if line_count >= min_lines:
        return None
    return (
        f"suspiciously collapsed into {line_count} LF-separated line(s); "
        f"expected at least {min_lines}"
    )


def min_lines_for_public_file(relative: str) -> int | None:
    normalized = normalize_relative(relative)
    if normalized in CRITICAL_MIN_LINES:
        return CRITICAL_MIN_LINES[normalized]
    if normalized.startswith(".github/workflows/") and normalized.endswith(".yml"):
        return 15
    if normalized.startswith(".github/") and normalized.endswith(".md"):
        return 10
    if normalized.startswith(".github/ISSUE_TEMPLATE/"):
        return 10
    return None


def generic_collapsed_text_file(relative: str, data: bytes, line_count: int) -> bool:
    """Return whether a text-like public file appears collapsed into one line."""
    normalized = normalize_relative(relative)
    suffix = PurePosixPath(normalized).suffix.lower()
    if suffix not in COLLAPSE_SUFFIXES and not normalized.endswith(
        COMPOUND_TEXT_SUFFIXES
    ):
        return False
    return len(data) >= 240 and line_count <= 1


def normalize_relative(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
