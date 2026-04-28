"""Runtime and artifact helpers for self-improvement workflows."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "default_loop_id",
    "read_json_object",
    "read_text",
    "resolve_optional_artifact_path",
    "utc_now",
    "write_json",
]


def resolve_optional_artifact_path(root: Path, value: str) -> Path | None:
    """Resolve an optional artifact path relative to the repository root."""
    text = value.strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON object artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object, returning an empty mapping for optional bad artifacts."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_text(path: Path) -> str:
    """Read text for optional documentation checks."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_loop_id(prefix: str, generated_at: str) -> str:
    """Build a compact loop id from a timestamp."""
    compact = generated_at.replace("-", "").replace(":", "").replace("T", "-")
    compact = compact.removesuffix("Z")
    return f"{prefix}-{compact}"
