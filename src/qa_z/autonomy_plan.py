"""Loop-health classification and plan rendering for autonomy workflows."""

from __future__ import annotations

from typing import Any

from qa_z.live_repository import render_live_repository_summary

__all__ = [
    "build_loop_health",
    "render_autonomy_loop_plan",
]


def build_loop_health(
    *,
    selected_count: int,
    fallback_selected: bool,
    selection_gap_reason: str | None,
    backlog_open_count_before_inspection: int,
    backlog_open_count_after_inspection: int,
    blocked_chain_length: int = 0,
    blocked_chain_loop_ids: list[str] | None = None,
    blocked_stop_threshold: int = 0,
) -> dict[str, Any]:
    """Build a compact loop-health summary for outcome, history, and status."""
    taskless = selected_count == 0
    if taskless:
        classification = "taskless"
    elif fallback_selected:
        classification = "fallback_selected"
    else:
        classification = "selected"
    stale_open_items_closed = max(
        backlog_open_count_before_inspection - backlog_open_count_after_inspection,
        0,
    )
    return {
        "classification": classification,
        "selected_count": max(selected_count, 0),
        "taskless": taskless,
        "fallback_selected": bool(fallback_selected),
        "selection_gap_reason": selection_gap_reason,
        "backlog_open_count_before_inspection": max(
            backlog_open_count_before_inspection, 0
        ),
        "backlog_open_count_after_inspection": max(
            backlog_open_count_after_inspection, 0
        ),
        "stale_open_items_closed": stale_open_items_closed,
        "blocked_chain_length": max(blocked_chain_length, 0),
        "blocked_chain_loop_ids": [
            str(loop_id)
            for loop_id in (blocked_chain_loop_ids or [])
            if str(loop_id).strip()
        ],
        "blocked_chain_remaining_until_stop": max(
            blocked_stop_threshold - blocked_chain_length,
            0,
        )
        if blocked_chain_length > 0 and blocked_stop_threshold > 0
        else 0,
        "summary": loop_health_summary_text(
            classification=classification,
            selected_count=selected_count,
            fallback_selected=fallback_selected,
            stale_open_items_closed=stale_open_items_closed,
            backlog_open_count_before_inspection=backlog_open_count_before_inspection,
            backlog_open_count_after_inspection=backlog_open_count_after_inspection,
            blocked_chain_length=blocked_chain_length,
            blocked_stop_threshold=blocked_stop_threshold,
        ),
    }


def loop_health_summary_text(
    *,
    classification: str,
    selected_count: int,
    fallback_selected: bool,
    stale_open_items_closed: int,
    backlog_open_count_before_inspection: int,
    backlog_open_count_after_inspection: int,
    blocked_chain_length: int,
    blocked_stop_threshold: int,
) -> str:
    """Render one deterministic loop-health summary sentence."""
    blocked_chain_suffix = ""
    if blocked_chain_length > 0 and blocked_stop_threshold > 0:
        blocked_chain_suffix = (
            f"; blocked no-candidate chain {blocked_chain_length}/"
            f"{blocked_stop_threshold}"
        )
    if classification == "taskless":
        if stale_open_items_closed:
            suffix = "item" if stale_open_items_closed == 1 else "items"
            return (
                f"self-inspection closed {stale_open_items_closed} stale open "
                f"backlog {suffix}; no replacement fallback candidates were selected"
                f"{blocked_chain_suffix}"
            )
        if backlog_open_count_before_inspection <= 0:
            return (
                "no open backlog items before inspection and no fallback candidates "
                f"were generated{blocked_chain_suffix}"
            )
        if backlog_open_count_after_inspection > 0:
            return (
                "open backlog items remained but selection produced no task"
                f"{blocked_chain_suffix}"
            )
        return f"no evidence-backed backlog items survived inspection{blocked_chain_suffix}"
    if fallback_selected:
        return f"fallback selection produced {max(selected_count, 0)} task(s)"
    return f"selected {max(selected_count, 0)} open backlog task(s)"


def render_autonomy_loop_plan(
    *,
    loop_id: str,
    generated_at: str,
    selected_tasks: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    selected_fallback_families: list[str] | None = None,
    selection_gap_reason: str | None = None,
    backlog_open_count_before_inspection: int | None = None,
    backlog_open_count_after_inspection: int | None = None,
    loop_health: dict[str, Any] | None = None,
    live_repository: object | None = None,
) -> str:
    """Render the human next-action packet for one autonomy loop."""
    fallback_families = [
        str(item)
        for item in (selected_fallback_families or [])
        if isinstance(item, str) and item.strip()
    ]
    lines = [
        "# QA-Z Autonomy Loop Plan",
        "",
        f"- Loop id: `{loop_id}`",
        f"- Generated at: `{generated_at}`",
        "- Boundary: QA-Z prepares plans and local sessions only.",
        "- It does not edit code, call Codex or Claude APIs, schedule jobs, commit, or push.",
    ]
    if fallback_families:
        lines.append(
            "- Selected fallback families: "
            + ", ".join(f"`{family}`" for family in fallback_families)
        )
    if isinstance(live_repository, dict):
        lines.extend(
            [
                "",
                "## Live Repository Context",
                "",
                f"- {render_live_repository_summary(live_repository)}",
            ]
        )
    lines.extend(["", "## Selected Tasks", ""])
    if not selected_tasks:
        lines.append("- No open backlog tasks were selected.")
        if loop_health:
            lines.append(
                f"- Loop health: `{loop_health.get('classification', 'unknown')}`"
            )
            if loop_health.get("summary"):
                lines.append(f"- Loop health summary: {loop_health['summary']}")
            if loop_health.get("blocked_chain_length"):
                lines.append(
                    "- Blocked no-candidate chain: "
                    f"{loop_health.get('blocked_chain_length')}/"
                    f"{max(loop_health.get('blocked_chain_length', 0) + loop_health.get('blocked_chain_remaining_until_stop', 0), 0)}"
                )
            blocked_chain_loop_ids = [
                str(loop_id)
                for loop_id in loop_health.get("blocked_chain_loop_ids", [])
                if str(loop_id).strip()
            ]
            if blocked_chain_loop_ids:
                lines.append(
                    "- Blocked no-candidate loop ids: "
                    + ", ".join(f"`{loop_id}`" for loop_id in blocked_chain_loop_ids)
                )
        if selection_gap_reason:
            lines.append(f"- Selection gap reason: `{selection_gap_reason}`")
        if (
            backlog_open_count_before_inspection is not None
            and backlog_open_count_after_inspection is not None
        ):
            lines.append(
                "- Open backlog count: "
                f"{backlog_open_count_before_inspection} before inspection, "
                f"{backlog_open_count_after_inspection} after inspection"
            )
    for index, task in enumerate(selected_tasks, start=1):
        lines.extend(
            [
                f"{index}. {task.get('title', task.get('id', 'untitled'))}",
                f"   - id: `{task.get('id', '')}`",
                f"   - category: `{task.get('category', '')}`",
                f"   - recommendation: `{task.get('recommendation', '')}`",
                f"   - priority score: {task.get('priority_score', 0)}",
            ]
        )
        if task.get("selection_priority_score") is not None:
            lines.append(
                f"   - selection score: {task.get('selection_priority_score', 0)}"
            )
        selection_penalty = task.get("selection_penalty")
        penalty_reasons = [
            str(reason)
            for reason in task.get("selection_penalty_reasons", [])
            if isinstance(reason, str) and reason.strip()
        ]
        if selection_penalty:
            if penalty_reasons:
                lines.append(
                    "   - selection penalty: "
                    f"{selection_penalty} "
                    f"({', '.join(f'`{reason}`' for reason in penalty_reasons)})"
                )
            else:
                lines.append(f"   - selection penalty: {selection_penalty}")
        evidence = task.get("evidence")
        lines.append("   - evidence:")
        if not isinstance(evidence, list) or not evidence:
            lines.append("     - none recorded")
        else:
            for entry in evidence:
                if not isinstance(entry, dict):
                    continue
                lines.append(
                    "     - "
                    f"{entry.get('source', 'artifact')}: "
                    f"`{entry.get('path', 'unknown')}` "
                    f"{entry.get('summary', '')}".rstrip()
                )
    lines.extend(["", "## Prepared Actions", ""])
    if not actions:
        lines.append("- No action was prepared because no task was selected.")
    for action in actions:
        lines.extend(
            [
                f"- `{action.get('type')}` for `{action.get('task_id')}`",
                f"  - {action.get('title')}",
                f"  - next: {action.get('next_recommendation')}",
            ]
        )
        if action.get("session_id"):
            lines.append(f"  - session: `{action['session_id']}`")
        commands = action.get("commands")
        if isinstance(commands, list) and commands:
            lines.append("  - commands:")
            for command in commands:
                lines.append(f"    - `{command}`")
        context_paths = action.get("context_paths")
        if isinstance(context_paths, list) and context_paths:
            lines.append("  - context:")
            for path in context_paths:
                lines.append(f"    - `{path}`")
    lines.extend(
        [
            "",
            "## Next Loop Input",
            "",
            "- After external repair or docs/fixture work, rerun verification or benchmark evidence.",
            "- Run `python -m qa_z autonomy --loops 1` to record the next planning step.",
        ]
    )
    return "\n".join(lines).strip() + "\n"
