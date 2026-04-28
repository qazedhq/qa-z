"""Task selection surface for scoring and operator-facing summaries."""

__all__ = [
    "apply_selection_penalty",
    "compact_backlog_evidence_summary",
    "evidence_paths",
    "fallback_families_for_items",
    "fallback_family_for_category",
    "render_loop_plan",
    "select_items_with_batch_diversity",
    "selected_task_action_hint",
    "selected_task_fallback_families",
    "selected_task_validation_command",
    "worktree_action_areas",
]
from qa_z.task_selection_core import (
    apply_selection_penalty,
    evidence_paths,
    fallback_families_for_items,
    fallback_family_for_category,
    select_items_with_batch_diversity,
    selected_task_fallback_families,
)
from qa_z.task_selection_evidence import (
    compact_backlog_evidence_summary,
    worktree_action_areas,
)
from qa_z.task_selection_render import (
    render_loop_plan,
    selected_task_action_hint,
    selected_task_validation_command,
)
