"""Selection workflow helpers for self-improvement backlog planning."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qa_z.artifacts import format_path
from qa_z.backlog_core import OPEN_STATUSES
from qa_z.improvement_state import (
    append_history,
    backlog_file,
    load_backlog,
    load_history_entries,
)
from qa_z.selection_context import latest_self_inspection_selection_context
from qa_z.self_improvement_constants import SELF_IMPROVEMENT_SCHEMA_VERSION
from qa_z.self_improvement_runtime import default_loop_id, utc_now, write_json
from qa_z.task_selection import (
    apply_selection_penalty,
    compact_backlog_evidence_summary,
    render_loop_plan,
    select_items_with_batch_diversity,
    selected_task_action_hint,
    selected_task_validation_command,
)

__all__ = [
    "SelectionArtifactPaths",
    "select_next_tasks",
]

SELECTED_TASKS_KIND = "qa_z.selected_tasks"
RECENT_SELECTION_WINDOW = 2


@dataclass(frozen=True)
class SelectionArtifactPaths:
    """Paths written by a select-next pass."""

    selected_tasks_path: Path
    loop_plan_path: Path
    history_path: Path


def select_next_tasks(
    *,
    root: Path,
    count: int = 3,
    now: str | None = None,
    loop_id: str | None = None,
) -> SelectionArtifactPaths:
    """Select the next highest-value open backlog items and persist loop memory."""
    root = root.resolve()
    generated_at = now or utc_now()
    resolved_loop_id = loop_id or default_loop_id("loop", generated_at)
    backlog = load_backlog(root)
    selected_count = min(max(count, 1), 3)
    open_items = [
        item
        for item in backlog.get("items", [])
        if isinstance(item, dict) and str(item.get("status", "open")) in OPEN_STATUSES
    ]
    history_path = root / ".qa-z" / "loops" / "history.jsonl"
    recent_entries = load_history_entries(history_path)[-RECENT_SELECTION_WINDOW:]
    scored_items = [
        apply_selection_penalty(
            item, recent_entries=recent_entries, open_items=open_items
        )
        for item in open_items
    ]
    selected_items = select_items_with_batch_diversity(
        scored_items=scored_items,
        count=selected_count,
    )
    selected_items = [
        selected_task_with_operator_hints(item) for item in selected_items
    ]
    open_backlog_count = len(open_items)
    selection_gap_reason = selection_gap_reason_for_selected_items(
        selected_items=selected_items,
        open_backlog_count=open_backlog_count,
    )
    selection_state = (
        "blocked_no_candidates" if selection_gap_reason is not None else None
    )
    selection_context = latest_self_inspection_selection_context(root)

    latest_dir = root / ".qa-z" / "loops" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    selected_tasks_path = latest_dir / "selected_tasks.json"
    loop_plan_path = latest_dir / "loop_plan.md"

    selected_artifact = {
        "kind": SELECTED_TASKS_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "loop_id": resolved_loop_id,
        "generated_at": generated_at,
        "source_backlog": format_path(backlog_file(root), root),
        "selected_tasks": selected_items,
    }
    if selection_gap_reason:
        selected_artifact["state"] = selection_state
        selected_artifact["selection_gap_reason"] = selection_gap_reason
        selected_artifact["open_backlog_count"] = open_backlog_count
    selected_artifact.update(selection_context)
    write_json(selected_tasks_path, selected_artifact)
    loop_plan_path.write_text(
        render_loop_plan(
            loop_id=resolved_loop_id,
            generated_at=generated_at,
            selected_items=selected_items,
            live_repository=selection_context.get("live_repository"),
            state=selection_state,
            selection_gap_reason=selection_gap_reason,
            open_backlog_count=(
                open_backlog_count if selection_gap_reason is not None else None
            ),
        ),
        encoding="utf-8",
    )
    append_history(
        history_path,
        loop_id=resolved_loop_id,
        generated_at=generated_at,
        selected_items=selected_items,
        open_items=scored_items,
        selection_context=selection_context,
        state=selection_state,
        selection_gap_reason=selection_gap_reason,
        open_backlog_count=(
            open_backlog_count if selection_gap_reason is not None else None
        ),
    )
    return SelectionArtifactPaths(
        selected_tasks_path=selected_tasks_path,
        loop_plan_path=loop_plan_path,
        history_path=history_path,
    )


def selected_task_with_operator_hints(item: dict[str, object]) -> dict[str, object]:
    """Return a selected task copy with deterministic operator hints attached."""
    enriched = dict(item)
    enriched["action_hint"] = selected_task_action_hint(enriched)
    enriched["validation_command"] = selected_task_validation_command(enriched)
    enriched["evidence_summary"] = compact_backlog_evidence_summary(enriched)
    return enriched


def selection_gap_reason_for_selected_items(
    *,
    selected_items: list[dict[str, object]],
    open_backlog_count: int,
) -> str | None:
    """Return a compact reason when select-next cannot emit a task."""
    if selected_items:
        return None
    if open_backlog_count <= 0:
        return "no_open_backlog_after_inspection"
    return "open_backlog_items_not_selected"
