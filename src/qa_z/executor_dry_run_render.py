"""Operator-facing rendering helpers for executor dry-run surfaces."""

from __future__ import annotations
from typing import cast

from qa_z.operator_action_render import render_recommended_action_lines


def render_dry_run_report(summary: dict[str, object]) -> str:
    """Render the operator-facing dry-run report."""
    rule_status_counts = cast(
        dict[str, object], summary.get("rule_status_counts") or {}
    )
    signals = [
        text
        for item in cast(list[object], summary.get("history_signals") or [])
        if (text := str(item).strip())
    ]
    lines = [
        "# QA-Z Executor Result Dry-Run",
        "",
        f"- Session: `{summary['session_id']}`",
        f"- Source: `{summary.get('summary_source') or 'unknown'}`",
        f"- Verdict: `{summary['verdict']}`",
        f"- Why: `{summary.get('verdict_reason') or 'history_clear'}`",
        f"- Attempts: `{summary['evaluated_attempt_count']}`",
        f"- Latest attempt: `{summary.get('latest_attempt_id') or 'none'}`",
        f"- Safety package: `{summary.get('safety_package_id') or 'unknown'}`",
        f"- Operator decision: `{summary.get('operator_decision') or 'not recorded'}`",
        f"- Operator summary: {summary.get('operator_summary') or 'not recorded'}",
        f"- Next: {summary['next_recommendation']}",
        (
            "- Rule counts: "
            f"clear={rule_status_counts.get('clear', 0)}, "
            f"attention={rule_status_counts.get('attention', 0)}, "
            f"blocked={rule_status_counts.get('blocked', 0)}"
        ),
        "",
        "## History Signals",
        "",
    ]
    if not signals:
        lines.append("- none")
    else:
        for signal in signals:
            lines.append(f"- `{signal}`")
    lines.extend(["", "## Recommended Actions", ""])
    lines.extend(render_recommended_action_lines(summary.get("recommended_actions")))
    lines.extend(["", "## Rule Evaluations", ""])
    for rule in cast(list[object], summary.get("rule_evaluations") or []):
        if not isinstance(rule, dict):
            continue
        lines.append(
            f"- `{rule.get('id', 'unknown')}` -> `{rule.get('status', 'clear')}`: {rule.get('summary', '').strip()}"
        )
    return "\n".join(lines).strip() + "\n"


def normalize_recommended_actions(value: object) -> list[dict[str, str]]:
    """Return recommended action objects from optional dry-run payload data."""
    if not isinstance(value, list):
        return []
    actions: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action_id = str(item.get("id") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if action_id and summary:
            actions.append({"id": action_id, "summary": summary})
    return actions
