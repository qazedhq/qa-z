"""Structured models for changed files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ChangeStatus = Literal["added", "modified", "deleted", "renamed"]
FileLanguage = Literal[
    "python", "typescript", "markdown", "toml", "yaml", "json", "other"
]
FileKind = Literal["source", "test", "config", "docs", "other"]
ChangeSource = Literal["cli_diff", "contract", "none"]


@dataclass(slots=True)
class ChangedFile:
    """One changed file with enough metadata for deterministic selectors."""

    path: str
    old_path: str | None
    status: ChangeStatus
    additions: int
    deletions: int
    language: FileLanguage
    kind: FileKind

    def to_dict(self) -> dict[str, Any]:
        """Render this changed file as JSON/YAML-safe data."""
        return {
            "path": self.path,
            "old_path": self.old_path,
            "status": self.status,
            "additions": self.additions,
            "deletions": self.deletions,
            "language": self.language,
            "kind": self.kind,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChangedFile":
        """Load one changed-file entry from artifact metadata."""
        return cls(
            path=str(data["path"]),
            old_path=str(data["old_path"])
            if data.get("old_path") is not None
            else None,
            status=coerce_literal(
                data.get("status"),
                {"added", "modified", "deleted", "renamed"},
                "modified",
            ),
            additions=coerce_int(data.get("additions")),
            deletions=coerce_int(data.get("deletions")),
            language=coerce_literal(
                data.get("language"),
                {"python", "typescript", "markdown", "toml", "yaml", "json", "other"},
                "other",
            ),
            kind=coerce_literal(
                data.get("kind"),
                {"source", "test", "config", "docs", "other"},
                "other",
            ),
        )


@dataclass(slots=True)
class ChangeSet:
    """A collection of changed files and where it came from."""

    source: ChangeSource
    files: list[ChangedFile] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        """Return whether this change set contains any files."""
        return not self.files

    def to_dict(self) -> dict[str, Any]:
        """Render this change set as JSON/YAML-safe data."""
        return {
            "source": self.source,
            "files": [changed.to_dict() for changed in self.files],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChangeSet":
        """Load a change set from artifact metadata."""
        files = data.get("files")
        if not isinstance(files, list):
            raise ValueError("Change set files must be a list.")
        return cls(
            source=coerce_literal(
                data.get("source"),
                {"cli_diff", "contract", "none"},
                "contract",
            ),
            files=[
                ChangedFile.from_dict(item) for item in files if isinstance(item, dict)
            ],
        )


def coerce_int(value: Any) -> int:
    """Coerce artifact numeric fields to non-negative integers."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(number, 0)


def coerce_literal(value: Any, allowed: set[str], default: str) -> Any:
    """Coerce a loose artifact value to an allowed string literal."""
    text = str(value) if value is not None else ""
    return text if text in allowed else default
