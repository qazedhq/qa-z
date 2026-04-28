"""Shared path, timestamp, and JSON helpers for executor-ingest flows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError


def current_utc_timestamp() -> str:
    """Return a stable UTC timestamp string for ingest bookkeeping."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def resolve_relative_path(root: Path, value: str | Path) -> Path:
    """Resolve a path relative to the repository root when needed."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def format_relative_path(path: Path, root: Path) -> str:
    """Return a slash-separated path relative to root when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def normalize_repo_path(value: str) -> str:
    """Normalize a repository-relative path to slash-separated text."""
    return value.replace("\\", "/").strip().strip("/")


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a required JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactLoadError(
            f"Could not read executor-ingest artifact: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(
            f"Executor-ingest artifact is not valid JSON: {path}"
        ) from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError(f"Executor-ingest artifact must be an object: {path}")
    return data


def optional_text(value: object) -> str | None:
    """Return stripped text or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse a UTC-ish timestamp conservatively."""
    text = optional_text(value)
    if text is None:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
