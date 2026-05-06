"""Check tracked public text files for portable line endings and layout."""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
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
    "README.md": 20,
    "pyproject.toml": 20,
    "qa-z.yaml.example": 40,
    ".gitattributes": 8,
    ".editorconfig": 8,
}


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
    args = parser.parse_args(argv)
    root = Path(args.path).expanduser().resolve()
    issues = check_paths(root, tracked_paths(root))
    if not issues:
        print("text file hygiene passed")
        return 0
    print("text file hygiene failed")
    for issue in issues:
        print(f"- {issue.path}: {issue.reason}")
    return 1


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


def check_paths(root: Path, paths: Iterable[Path]) -> list[HygieneIssue]:
    """Check a provided path set and return all hygiene issues."""
    issues: list[HygieneIssue] = []
    for path in sorted(paths, key=lambda item: relative_path(root, item)):
        if not path.is_file():
            continue
        relative = relative_path(root, path)
        data = path.read_bytes()
        if should_skip_binary(path, data):
            continue
        if b"\0" in data:
            issues.append(HygieneIssue(relative, "contains NUL bytes"))
            continue
        if b"\r\n" in data:
            issues.append(HygieneIssue(relative, "contains CRLF line endings"))
            continue
        if b"\r" in data:
            issues.append(HygieneIssue(relative, "contains CR-only line endings"))
            continue
        collapsed_reason = collapsed_public_file_reason(relative, data)
        if collapsed_reason:
            issues.append(HygieneIssue(relative, collapsed_reason))
    return issues


def should_skip_binary(path: Path, data: bytes) -> bool:
    """Return whether a path should be treated as binary for this check."""
    suffix = path.suffix.lower()
    if suffix in BINARY_SUFFIXES:
        return True
    if is_text_path(path):
        return False
    if b"\0" in data:
        return True
    return False


def is_text_path(path: Path) -> bool:
    """Return whether a path is expected to be text by name or suffix."""
    name = path.name.lower()
    if name in {".editorconfig", ".gitattributes", ".gitignore"}:
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def collapsed_public_file_reason(relative: str, data: bytes) -> str | None:
    """Return a reason when a critical public file looks line-collapsed."""
    min_lines = min_lines_for_public_file(relative)
    if min_lines is None:
        return None
    line_count = data.decode("utf-8", errors="replace").count("\n")
    if line_count >= min_lines:
        return None
    if len(data) < 120:
        return None
    return f"suspiciously collapsed into {line_count} line(s); expected at least {min_lines}"


def min_lines_for_public_file(relative: str) -> int | None:
    normalized = relative.replace("\\", "/")
    if normalized in CRITICAL_MIN_LINES:
        return CRITICAL_MIN_LINES[normalized]
    if normalized.startswith(".github/workflows/") and normalized.endswith(".yml"):
        return 6
    if normalized.startswith(".github/") and normalized.endswith(".md"):
        return 4
    if normalized.startswith(".github/ISSUE_TEMPLATE/"):
        return 4
    return None


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
