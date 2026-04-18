"""Best-effort unified diff parser for QA-Z change metadata."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from qa_z.diffing.models import (
    ChangedFile,
    ChangeSet,
    ChangeSource,
    ChangeStatus,
    FileKind,
    FileLanguage,
)

DIFF_HEADER = re.compile(r"^diff --git (?P<old>.+?) (?P<new>.+)$")

TYPESCRIPT_SUFFIXES = {".ts", ".tsx", ".cts", ".mts"}
TYPESCRIPT_CONFIG_NAMES = {
    ".eslintrc.cjs",
    ".eslintrc.js",
    ".eslintrc.json",
    ".eslintrc.mjs",
    ".eslintrc.yaml",
    ".eslintrc.yml",
    "eslint.config.cjs",
    "eslint.config.js",
    "eslint.config.mjs",
    "package-lock.json",
    "package.json",
    "pnpm-lock.yaml",
    "tsconfig.base.json",
    "tsconfig.json",
    "vite.config.cjs",
    "vite.config.js",
    "vite.config.mjs",
    "vite.config.ts",
    "vitest.config.cjs",
    "vitest.config.js",
    "vitest.config.mjs",
    "vitest.config.ts",
    "yarn.lock",
}


def parse_unified_diff(
    text: str | None, *, source: ChangeSource = "cli_diff"
) -> ChangeSet | None:
    """Parse a git-style unified diff into a structured change set.

    Returns ``None`` for non-empty malformed input so callers can conservatively
    escalate to full checks. Empty input is a valid empty change set.
    """
    if text is None or not text.strip():
        return ChangeSet(source=source, files=[])

    lines = text.splitlines()
    header_indexes = [
        index for index, line in enumerate(lines) if DIFF_HEADER.match(line)
    ]
    if not header_indexes:
        return None

    files: list[ChangedFile] = []
    for position, start in enumerate(header_indexes):
        end = (
            header_indexes[position + 1]
            if position + 1 < len(header_indexes)
            else len(lines)
        )
        parsed = parse_file_block(lines[start:end])
        if parsed is None:
            return None
        files.append(parsed)
    return ChangeSet(source=source, files=files)


def parse_file_block(lines: list[str]) -> ChangedFile | None:
    """Parse one ``diff --git`` block."""
    if not lines:
        return None
    header = DIFF_HEADER.match(lines[0])
    if header is None:
        return None

    old_from_header = strip_diff_prefix(header.group("old"))
    new_from_header = strip_diff_prefix(header.group("new"))
    old_path: str | None = old_from_header
    path = new_from_header
    status: ChangeStatus = "modified"
    additions = 0
    deletions = 0

    for line in lines[1:]:
        if line.startswith("new file mode"):
            status = "added"
            old_path = None
        elif line.startswith("deleted file mode"):
            status = "deleted"
            path = old_from_header
            old_path = old_from_header
        elif line.startswith("rename from "):
            status = "renamed"
            old_path = normalize_diff_path(line.removeprefix("rename from "))
        elif line.startswith("rename to "):
            status = "renamed"
            path = normalize_diff_path(line.removeprefix("rename to "))
        elif line.startswith("--- "):
            marker = line.removeprefix("--- ").strip()
            if marker == "/dev/null":
                status = "added"
                old_path = None
            elif status != "renamed":
                old_path = strip_diff_prefix(marker)
        elif line.startswith("+++ "):
            marker = line.removeprefix("+++ ").strip()
            if marker == "/dev/null":
                status = "deleted"
                path = old_path or old_from_header
            elif status != "renamed":
                path = strip_diff_prefix(marker)
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1

    normalized_path = normalize_diff_path(path)
    normalized_old_path = normalize_diff_path(old_path) if old_path else None
    language = infer_language(normalized_path)
    return ChangedFile(
        path=normalized_path,
        old_path=normalized_old_path,
        status=status,
        additions=additions,
        deletions=deletions,
        language=language,
        kind=infer_kind(normalized_path, language),
    )


def strip_diff_prefix(value: str) -> str:
    """Remove git diff ``a/`` or ``b/`` prefixes and quotes."""
    normalized = normalize_diff_path(value)
    if normalized.startswith(("a/", "b/")):
        return normalized[2:]
    return normalized


def normalize_diff_path(value: str) -> str:
    """Normalize a diff path into slash-separated repo-relative form."""
    path = value.strip().strip('"').replace("\\", "/")
    return path


def infer_language(path: str) -> FileLanguage:
    """Infer a coarse language from a changed path."""
    suffix = PurePosixPath(path).suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in TYPESCRIPT_SUFFIXES:
        return "typescript"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix == ".toml":
        return "toml"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    if suffix == ".json":
        return "json"
    return "other"


def infer_kind(path: str, language: FileLanguage) -> FileKind:
    """Infer a broad file kind for selector decisions."""
    normalized = path.replace("\\", "/").lower()
    name = PurePosixPath(normalized).name
    if name in TYPESCRIPT_CONFIG_NAMES:
        return "config"
    if (
        normalized.startswith("docs/")
        or normalized.startswith("doc/")
        or name in {"readme.md", "changelog.md"}
        or language == "markdown"
    ):
        return "docs"
    if (
        name in {"qa-z.yaml", "qa-z.yml", "pyproject.toml", "mypy.ini"}
        or normalized.startswith(".github/")
        or normalized.startswith("config/")
    ):
        return "config"
    if language == "python" and (
        normalized.startswith("tests/")
        or "/tests/" in normalized
        or name.startswith("test_")
        or name.endswith("_test.py")
    ):
        return "test"
    if language == "python":
        return "source"
    if language == "typescript" and (
        normalized.startswith("tests/")
        or normalized.startswith("__tests__/")
        or "/tests/" in normalized
        or "/__tests__/" in normalized
        or ".test." in name
        or ".spec." in name
    ):
        return "test"
    if language == "typescript":
        return "source"
    return "other"
