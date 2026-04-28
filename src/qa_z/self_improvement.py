"""Self-inspection and improvement backlog artifacts for QA-Z."""

from __future__ import annotations

from qa_z.backlog_core import (
    BacklogCandidate,
    int_value,
    score_candidate,
    slugify,
)
from qa_z.benchmark_signals import (
    benchmark_summary_snapshot as _benchmark_summary_snapshot,
)
from qa_z.execution_discovery import (
    discover_executor_contract_candidates,
    discover_executor_history_candidates,
    discover_executor_ingest_candidates,
    discover_executor_result_candidates,
    discover_session_candidates,
    discover_verification_candidates,
)
from qa_z.improvement_state import (
    load_backlog as _load_backlog,
    open_backlog_items as _open_backlog_items,
)
from qa_z.live_repository import (
    classify_worktree_path_area as _classify_worktree_path_area,
    collect_live_repository_signals,
    empty_live_repository_signals as _empty_live_repository_signals,
    git_current_branch as _git_current_branch,
    git_current_head as _git_current_head,
    git_worktree_snapshot as _git_worktree_snapshot,
    is_runtime_artifact_path as _is_runtime_artifact_path,
    live_repository_summary,
    render_live_repository_summary as _render_live_repository_summary,
)
from qa_z.self_improvement_constants import (
    SELF_IMPROVEMENT_SCHEMA_VERSION,
)
from qa_z.self_improvement_discovery import (
    discover_backlog_reseeding_candidates,
    discover_benchmark_candidates,
    discover_empty_loop_candidates,
    discover_repeated_fallback_family_candidates,
)
from qa_z.self_improvement_inspection import (
    SelfInspectionArtifactPaths,
    run_self_inspection,
)
from qa_z.self_improvement_registry import DISCOVERY_STAGE_NAMES
from qa_z.self_improvement_selection import SelectionArtifactPaths, select_next_tasks
from qa_z.surface_discovery import (
    discover_artifact_consistency_candidates,
    discover_coverage_gap_candidates,
    discover_docs_drift_candidates,
)
from qa_z.task_selection import (
    compact_backlog_evidence_summary as _compact_backlog_evidence_summary,
    evidence_paths,
    fallback_families_for_items,
    fallback_family_for_category as _fallback_family_for_category,
    render_loop_plan as _render_loop_plan,
    selected_task_action_hint as _selected_task_action_hint,
    selected_task_validation_command as _selected_task_validation_command,
    worktree_action_areas as _worktree_action_areas,
)
from qa_z.worktree_discovery import (
    discover_artifact_hygiene_candidates,
    discover_commit_isolation_candidates,
    discover_deferred_cleanup_candidates,
    discover_evidence_freshness_candidates,
    discover_integration_gap_candidates,
    discover_runtime_artifact_cleanup_candidates,
    discover_worktree_risk_candidates,
)

classify_worktree_path_area = _classify_worktree_path_area
compact_backlog_evidence_summary = _compact_backlog_evidence_summary
benchmark_summary_snapshot = _benchmark_summary_snapshot
empty_live_repository_signals = _empty_live_repository_signals
fallback_family_for_category = _fallback_family_for_category
git_current_branch = _git_current_branch
git_current_head = _git_current_head
git_worktree_snapshot = _git_worktree_snapshot
is_runtime_artifact_path = _is_runtime_artifact_path
load_backlog = _load_backlog
open_backlog_items = _open_backlog_items
render_live_repository_summary = _render_live_repository_summary
render_loop_plan = _render_loop_plan
selected_task_action_hint = _selected_task_action_hint
selected_task_validation_command = _selected_task_validation_command
worktree_action_areas = _worktree_action_areas

__all__ = [
    "BacklogCandidate",
    "SELF_IMPROVEMENT_SCHEMA_VERSION",
    "SelectionArtifactPaths",
    "SelfInspectionArtifactPaths",
    "benchmark_summary_snapshot",
    "classify_worktree_path_area",
    "collect_live_repository_signals",
    "compact_backlog_evidence_summary",
    "DISCOVERY_STAGE_NAMES",
    "discover_artifact_hygiene_candidates",
    "evidence_paths",
    "fallback_families_for_items",
    "fallback_family_for_category",
    "int_value",
    "is_runtime_artifact_path",
    "live_repository_summary",
    "load_backlog",
    "open_backlog_items",
    "render_live_repository_summary",
    "render_loop_plan",
    "run_self_inspection",
    "score_candidate",
    "discover_artifact_consistency_candidates",
    "discover_backlog_reseeding_candidates",
    "discover_benchmark_candidates",
    "discover_commit_isolation_candidates",
    "discover_coverage_gap_candidates",
    "discover_deferred_cleanup_candidates",
    "discover_docs_drift_candidates",
    "discover_empty_loop_candidates",
    "discover_evidence_freshness_candidates",
    "discover_executor_contract_candidates",
    "discover_executor_history_candidates",
    "discover_executor_ingest_candidates",
    "discover_executor_result_candidates",
    "discover_integration_gap_candidates",
    "discover_repeated_fallback_family_candidates",
    "discover_runtime_artifact_cleanup_candidates",
    "discover_session_candidates",
    "discover_verification_candidates",
    "discover_worktree_risk_candidates",
    "select_next_tasks",
    "selected_task_action_hint",
    "selected_task_validation_command",
    "slugify",
    "worktree_action_areas",
]
