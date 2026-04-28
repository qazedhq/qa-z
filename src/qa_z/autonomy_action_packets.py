"""Shared packet builders for autonomy prepared actions."""

from __future__ import annotations

__all__ = ["prepared_action"]


def prepared_action(
    *,
    task_id: str,
    action_type: str,
    title: str,
    next_recommendation: str,
    commands: list[str],
    context_paths: list[str] | None = None,
) -> dict[str, object]:
    """Build a stable non-executing prepared action."""
    action: dict[str, object] = {
        "type": action_type,
        "task_id": task_id,
        "title": title,
        "commands": commands,
        "next_recommendation": next_recommendation,
    }
    if context_paths:
        action["context_paths"] = list(context_paths)
    return action
