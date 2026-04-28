"""Dry-run stdout helpers for executor-result runtime commands."""

from __future__ import annotations

from typing import Any


def render_executor_result_dry_run_stdout(summary: dict[str, Any]) -> str:
    """Render human stdout for executor-result dry-run."""
    lines = [
        f"qa-z executor-result dry-run: {summary['verdict']}",
        f"Session: {summary['session_id']}",
        f"Attempts: {summary['evaluated_attempt_count']}",
        f"Latest attempt: {summary.get('latest_attempt_id') or 'none'}",
        f"Source: {dry_run_text_field(summary.get('summary_source'), 'unknown')}",
        f"Why: {dry_run_text_field(summary.get('verdict_reason'), 'not_recorded')}",
    ]
    rule_counts = dry_run_rule_counts(summary.get("rule_status_counts"))
    if rule_counts:
        lines.append(f"Rule counts: {rule_counts}")
    operator_summary = str(summary.get("operator_summary") or "").strip()
    if operator_summary:
        lines.append(f"Diagnostic: {operator_summary}")
    operator_decision = str(summary.get("operator_decision") or "").strip()
    if operator_decision:
        lines.append(f"Decision: {operator_decision}")
    actions = dry_run_action_summaries(summary.get("recommended_actions"))
    for action in actions[:3]:
        lines.append(f"Action {action}")
    lines.append(f"Next: {summary['next_recommendation']}")
    return "\n".join(lines)


def dry_run_text_field(value: object, fallback: str) -> str:
    """Return a stable one-line dry-run stdout field."""
    text = str(value or "").strip()
    return text or fallback


def dry_run_rule_counts(value: object) -> str | None:
    """Return ordered dry-run rule counts for human stdout."""
    if not isinstance(value, dict):
        return None

    def count(name: str) -> int:
        raw = value.get(name, 0)
        if isinstance(raw, bool):
            return 0
        if isinstance(raw, int):
            return raw
        return 0

    return (
        f"clear={count('clear')}, attention={count('attention')}, "
        f"blocked={count('blocked')}"
    )


def dry_run_action_summaries(value: object) -> list[str]:
    """Return readable recommended dry-run actions from optional payload data."""
    if not isinstance(value, list):
        return []
    actions: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action_id = str(item.get("id") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if summary:
            prefix = f"{action_id}: " if action_id else ""
            actions.append(f"{prefix}{summary}")
    return actions
