"""Deterministic changed-file risk classification for guard auto-deep."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


RISK_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("auth", ("auth", "session", "permission", "acl", "oauth", "login")),
    ("security", ("security", "crypto", "token", "secret", "csrf", "xss")),
    ("data", ("migration", "schema", "database", "db/", "models/")),
    ("API behavior", ("/api/", "api/", "route", "endpoint", "controller")),
    ("infra", ("terraform", "docker", "k8s", ".github/workflows", "deploy")),
    ("public surface", ("readme", "docs/", "templates/", ".github/")),
)


@dataclass(frozen=True)
class ChangeRisk:
    """Risk categories inferred from changed files."""

    changed_files: list[str]
    categories: list[str]

    @property
    def needs_deep(self) -> bool:
        return bool(self.categories)


def classify_change_risk(changed_files: Iterable[str]) -> ChangeRisk:
    """Classify changed files into stable guard risk categories."""
    files = [normalize_path(path) for path in changed_files if str(path).strip()]
    categories: list[str] = []
    for category, patterns in RISK_PATTERNS:
        if any(matches_any(path, patterns) for path in files):
            categories.append(category)
    return ChangeRisk(changed_files=files, categories=categories)


def detect_changed_files(root: Path) -> list[str]:
    """Return changed and untracked paths from git, best effort."""
    commands = (
        ("git", "-C", str(root), "diff", "--name-only", "HEAD"),
        ("git", "-C", str(root), "ls-files", "--others", "--exclude-standard"),
    )
    paths: list[str] = []
    for command in commands:
        completed = subprocess.run(
            command,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode == 0:
            paths.extend(line.strip() for line in completed.stdout.splitlines())
    return unique(paths)


def matches_any(path: str, patterns: tuple[str, ...]) -> bool:
    lowered = path.lower()
    return any(pattern in lowered for pattern in patterns)


def normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").lstrip("./")


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = normalize_path(value)
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
