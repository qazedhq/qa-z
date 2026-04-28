"""Human-readable output helpers for self-improvement planning commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.improvement_state import open_backlog_items
from qa_z.self_improvement import (
    SelectionArtifactPaths,
    compact_backlog_evidence_summary,
    int_value,
    render_live_repository_summary,
    selected_task_action_hint,
    selected_task_validation_command,
)

__all__ = [
    "render_backlog",
    "render_select_next_stdout",
    "render_self_inspect_stdout",
]


def render_self_inspect_stdout(
    report: dict[str, Any],
    *,
    self_inspection_path: Path,
    backlog_path: Path,
    root: Path,
) -> str:
    """Render human stdout for qa-z self-inspect."""
    candidates = [
        item for item in report.get("candidates", []) if isinstance(item, dict)
    ]
    lines = [
        "qa-z self-inspect: wrote self-improvement artifacts",
        f"Self inspection: {self_inspection_path.relative_to(root).as_posix()}",
        f"Backlog: {backlog_path.relative_to(root).as_posix()}",
        f"Live repository: {format_live_repository_summary(report)}",
        f"Candidates: {len(candidates)}",
        "Top candidates:",
    ]
    reseeded_candidate_ids = [
        str(item)
        for item in report.get("reseeded_candidate_ids", [])
        if isinstance(item, str) and item.strip()
    ]
    if report.get("backlog_reseeded"):
        lines.insert(
            3,
            f"Backlog reseeded: yes ({len(reseeded_candidate_ids)} concrete task(s))",
        )
    if not candidates:
        lines.append("- none")
    top_candidates = sorted(
        candidates,
        key=lambda item: (-int_value(item.get("priority_score")), str(item.get("id"))),
    )
    for item in top_candidates[:3]:
        lines.extend(
            [
                f"- {item.get('id')}: {item.get('title', item.get('id', 'untitled'))}",
                f"  recommendation: {item.get('recommendation', '')}",
                f"  action: {selected_task_action_hint(item)}",
                f"  validation: {selected_task_validation_command(item)}",
                f"  priority score: {item.get('priority_score', 0)}",
                f"  evidence: {compact_backlog_evidence_summary(item)}",
            ]
        )
    return "\n".join(lines)


def format_live_repository_summary(report: dict[str, object]) -> str:
    """Render compact live repository state for human self-inspect output."""
    return render_live_repository_summary(report.get("live_repository"))


def render_select_next_stdout(
    selected: dict[str, Any],
    paths: SelectionArtifactPaths,
    root: Path,
    *,
    refreshed: bool = False,
) -> str:
    """Render human stdout for qa-z select-next."""
    items = [
        item for item in selected.get("selected_tasks", []) if isinstance(item, dict)
    ]
    lines = [
        "qa-z select-next: wrote loop planning artifacts",
        f"Selected tasks: {paths.selected_tasks_path.relative_to(root).as_posix()}",
        f"Loop plan: {paths.loop_plan_path.relative_to(root).as_posix()}",
        f"History: {paths.history_path.relative_to(root).as_posix()}",
        f"Count: {len(items)}",
    ]
    if refreshed:
        lines.insert(4, "Refreshed: yes")
    live_summary = render_live_repository_summary(selected.get("live_repository"))
    if live_summary:
        lines.append(f"Live repository: {live_summary}")
    lines.append("Selected task details:")
    if not items:
        lines.append("- none")
    for item in items:
        lines.append(
            f"- {item.get('id')}: {item.get('title', item.get('id', 'untitled'))}"
        )
        if item.get("recommendation"):
            lines.append(f"  recommendation: {item['recommendation']}")
        lines.append(f"  action: {selected_task_action_hint(item)}")
        lines.append(f"  validation: {selected_task_validation_command(item)}")
        selection_score = item.get(
            "selection_priority_score", item.get("priority_score")
        )
        if selection_score is not None:
            lines.append(f"  selection score: {selection_score}")
        selection_penalty = item.get("selection_penalty")
        penalty_reasons = [
            str(reason)
            for reason in item.get("selection_penalty_reasons", [])
            if isinstance(reason, str) and reason.strip()
        ]
        if selection_penalty:
            if penalty_reasons:
                lines.append(
                    "  selection penalty: "
                    f"{selection_penalty} ({', '.join(penalty_reasons)})"
                )
            else:
                lines.append(f"  selection penalty: {selection_penalty}")
        evidence_summary = compact_backlog_evidence_summary(item)
        if evidence_summary:
            lines.append(f"  evidence: {evidence_summary}")
    return "\n".join(lines)


def render_backlog(backlog: dict[str, Any], *, refreshed: bool = False) -> str:
    """Render a human backlog summary that focuses on active work."""
    items = [item for item in backlog.get("items", []) if isinstance(item, dict)]
    open_items = open_backlog_items(backlog)
    closed_items = [
        item
        for item in items
        if str(item.get("status", "open")) not in {"open", "selected", "in_progress"}
    ]
    freshness_guard_closures = sum(
        1
        for item in closed_items
        if str(item.get("closure_reason") or "") == "freshness_guard_not_satisfied"
    )
    lines = [
        f"qa-z backlog: {len(items)} item(s)",
        f"Updated: {backlog.get('updated_at') or backlog.get('generated_at') or 'unknown'}",
        f"Open items: {len(open_items)}",
    ]
    if refreshed:
        lines.insert(2, "Refreshed: yes")
    if not open_items:
        lines.append("- none")
    for item in open_items:
        lines.extend(
            [
                f"- {item.get('id')}: {item.get('title', item.get('id', 'untitled'))}",
                "  status: "
                f"{item.get('status', 'open')} | "
                f"priority: {item.get('priority_score', 0)} | "
                f"recommendation: {item.get('recommendation', '')}",
                f"  action: {selected_task_action_hint(item)}",
                f"  validation: {selected_task_validation_command(item)}",
                f"  evidence: {compact_backlog_evidence_summary(item)}",
            ]
        )
    lines.append(f"Closed items: {len(closed_items)}")
    if freshness_guard_closures:
        lines.append(f"Freshness-guard closures: {freshness_guard_closures}")
    lines.append(
        "- use `qa-z backlog --json` for the full history"
        if closed_items
        else "- no closed history recorded"
    )
    return "\n".join(lines)
