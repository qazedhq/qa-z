"""Support helpers for session-scoped executor-result history."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write one deterministic JSON artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def allocate_attempt_id(*, base: str, used_ids: set[str]) -> str:
    """Allocate a stable attempt id that does not collide within history."""
    candidate = base.strip() or "attempt"
    if candidate not in used_ids:
        return candidate
    index = 2
    while f"{candidate}-{index}" in used_ids:
        index += 1
    return f"{candidate}-{index}"


def legacy_attempt_base(result_payload: dict[str, Any]) -> str:
    """Build a stable attempt-id base for one backfilled legacy result."""
    bridge_id = str(result_payload.get("bridge_id") or "bridge").strip() or "bridge"
    created_at = str(result_payload.get("created_at") or "unknown")
    compact = "".join(
        character.lower() for character in created_at if character.isalnum()
    )
    return f"{slugify(bridge_id)}-{compact or 'unknown'}"


def slugify(value: str) -> str:
    """Create a stable identifier fragment."""
    cleaned = "".join(
        character.lower() if character.isalnum() else "-" for character in value.strip()
    )
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "unknown"


def resolve_path(root: Path, value: str) -> Path:
    """Resolve a path relative to the repository root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()
