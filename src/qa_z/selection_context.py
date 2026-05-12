"""Selection-context readers for self-improvement loop artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.operator_commands import SELECT_NEXT_REFRESH_COUNT_JSON_COMMAND
from qa_z.self_improvement_runtime import read_json_object

__all__ = [
    "latest_self_inspection_selection_context",
]

SELF_INSPECTION_KIND = "qa_z.self_inspection"


def latest_self_inspection_selection_context(
    root: Path, *, min_generated_at: str | None = None
) -> dict[str, Any]:
    """Return latest self-inspection context for downstream selection artifacts."""
    path = root / ".qa-z" / "loops" / "latest" / "self_inspect.json"
    payload = read_json_object(path)
    if payload.get("kind") != SELF_INSPECTION_KIND:
        return {}
    generated_at = str(payload.get("generated_at") or "").strip()
    if min_generated_at and (not generated_at or generated_at < min_generated_at):
        return stale_self_inspection_selection_context(
            root=root,
            path=path,
            payload=payload,
            generated_at=generated_at,
        )
    live_repository = payload.get("live_repository")
    if not isinstance(live_repository, dict):
        return {}
    context: dict[str, Any] = {
        "source_self_inspection": format_path(path, root),
        "live_repository": dict(live_repository),
    }
    add_self_inspection_provenance(context, payload, generated_at=generated_at)
    return context


def stale_self_inspection_selection_context(
    *,
    root: Path,
    path: Path,
    payload: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    """Return provenance-only context when self-inspection trails the backlog."""
    context: dict[str, Any] = {
        "source_self_inspection": format_path(path, root),
        "source_self_inspection_stale_for_backlog": True,
        "source_self_inspection_refresh_commands": [
            SELECT_NEXT_REFRESH_COUNT_JSON_COMMAND
        ],
    }
    add_self_inspection_provenance(context, payload, generated_at=generated_at)
    return context


def add_self_inspection_provenance(
    context: dict[str, Any],
    payload: dict[str, Any],
    *,
    generated_at: str | None = None,
) -> None:
    """Copy stable self-inspection provenance fields into selection context."""
    generated_value = generated_at
    for source_key, target_key in (
        ("loop_id", "source_self_inspection_loop_id"),
        ("generated_at", "source_self_inspection_generated_at"),
    ):
        value = (
            generated_value
            if source_key == "generated_at" and generated_value is not None
            else str(payload.get(source_key) or "").strip()
        )
        if value:
            context[target_key] = value
