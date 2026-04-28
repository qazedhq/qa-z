"""Shared rendering helpers for operator-facing recommended actions."""

from __future__ import annotations


def render_recommended_action_lines(
    value: object, *, include_action_label: bool = False
) -> list[str]:
    """Render deterministic recommended-action lines for Markdown surfaces."""
    if not isinstance(value, list):
        return ["- none"]
    actions = [
        {
            "id": str(item.get("id") or "").strip(),
            "summary": str(item.get("summary") or "").strip(),
        }
        for item in value
        if isinstance(item, dict)
    ]
    actions = [action for action in actions if action["id"] and action["summary"]]
    if not actions:
        return ["- none"]
    label = "Action " if include_action_label else ""
    return [f"- {label}`{action['id']}`: {action['summary']}" for action in actions]
