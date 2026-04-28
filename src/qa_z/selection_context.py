"""Selection-context readers for self-improvement loop artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.self_improvement_runtime import read_json_object

__all__ = [
    "latest_self_inspection_selection_context",
]

SELF_INSPECTION_KIND = "qa_z.self_inspection"


def latest_self_inspection_selection_context(root: Path) -> dict[str, Any]:
    """Return latest self-inspection context for downstream selection artifacts."""
    path = root / ".qa-z" / "loops" / "latest" / "self_inspect.json"
    payload = read_json_object(path)
    if payload.get("kind") != SELF_INSPECTION_KIND:
        return {}
    live_repository = payload.get("live_repository")
    if not isinstance(live_repository, dict):
        return {}
    context: dict[str, Any] = {
        "source_self_inspection": format_path(path, root),
        "live_repository": dict(live_repository),
    }
    for source_key, target_key in (
        ("loop_id", "source_self_inspection_loop_id"),
        ("generated_at", "source_self_inspection_generated_at"),
    ):
        value = str(payload.get(source_key) or "").strip()
        if value:
            context[target_key] = value
    return context
