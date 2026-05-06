"""Deterministic action mapping helpers for QA-Z autonomy loops."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.autonomy_action_cleanup import cleanup_action, workflow_gap_action
from qa_z.autonomy_action_context import (
    loop_local_self_inspection_context_paths,
    merge_context_paths,
    recommendation_context_paths,
    task_context_paths,
)
from qa_z.autonomy_action_packets import prepared_action
from qa_z.autonomy_action_sessions import (
    baseline_run_from_verify_evidence,
    executor_dry_run_command,
    existing_session_id,
    repair_session_action,
)
from qa_z.operator_commands import AUTONOMY_ONE_LOOP_COMMAND
from qa_z.operator_commands import AUTONOMY_STATUS_JSON_COMMAND
from qa_z.operator_commands import BENCHMARK_COMMAND
from qa_z.operator_commands import SELF_INSPECT_COMMAND
from qa_z.operator_commands import SELF_INSPECT_JSON_COMMAND
from qa_z.operator_commands import SELECT_NEXT_COUNT_JSON_COMMAND
from qa_z.task_selection_core import repeated_fallback_family_from_item

__all__ = [
    "action_for_task",
    "baseline_run_from_verify_evidence",
    "cleanup_action",
    "executor_dry_run_command",
    "existing_session_id",
    "merge_context_paths",
    "prepared_action",
    "recommendation_context_paths",
    "repair_session_action",
    "task_context_paths",
    "workflow_gap_action",
]


def action_for_task(
    *,
    root: Path,
    config: dict[str, Any] | None,
    loop_id: str,
    task: dict[str, Any],
    deps: Any | None = None,
) -> dict[str, Any]:
    """Translate one selected backlog task into a deterministic next action."""
    task_id = str(task.get("id") or "unknown")
    category = str(task.get("category") or "")
    recommendation = str(task.get("recommendation") or "")
    signals = {
        str(item)
        for item in task.get("signals", [])
        if isinstance(item, str) and item.strip()
    }
    session_id = existing_session_id(task)

    if category in {"benchmark_gap", "coverage_gap"}:
        return prepared_action(
            task_id=task_id,
            action_type="benchmark_fixture_plan",
            title="Add or repair benchmark fixture evidence.",
            next_recommendation="run qa-z benchmark after fixture updates",
            commands=[BENCHMARK_COMMAND],
        )
    if category == "policy_gap":
        return prepared_action(
            task_id=task_id,
            action_type="policy_fixture_plan",
            title="Add a deterministic policy fixture or policy expectation.",
            next_recommendation="rerun policy-focused benchmark fixtures",
            commands=[BENCHMARK_COMMAND],
        )
    if category in {"docs_drift", "schema_drift"}:
        return prepared_action(
            task_id=task_id,
            action_type="docs_sync_plan",
            title="Synchronize README, schema docs, and examples with artifacts.",
            next_recommendation="rerun self-inspection after docs sync",
            commands=[SELF_INSPECT_COMMAND],
        )
    if category in {"backlog_reseeding_gap", "autonomy_selection_gap"}:
        if recommendation == "improve_fallback_diversity":
            repeated_family = repeated_fallback_family_from_item(task)
            if repeated_family:
                title = (
                    f"Diversify repeated {repeated_family} fallback selections "
                    f"before more {repeated_family} work."
                )
                next_recommendation = (
                    f"surface and select a non-{repeated_family} fallback family "
                    f"before another {repeated_family} loop"
                )
            else:
                title = (
                    "Diversify repeated fallback selections before more repeat work."
                )
                next_recommendation = (
                    "surface and select a non-repeated fallback family before "
                    "another repeated-family loop"
                )
            return prepared_action(
                task_id=task_id,
                action_type="loop_health_plan",
                title=title,
                next_recommendation=next_recommendation,
                commands=[
                    SELF_INSPECT_JSON_COMMAND,
                    SELECT_NEXT_COUNT_JSON_COMMAND,
                    AUTONOMY_ONE_LOOP_COMMAND,
                    AUTONOMY_STATUS_JSON_COMMAND,
                ],
                context_paths=merge_context_paths(
                    task_context_paths(task),
                    recommendation_context_paths(recommendation),
                    loop_local_self_inspection_context_paths(root, loop_id),
                ),
            )
        return prepared_action(
            task_id=task_id,
            action_type="loop_health_plan",
            title="Strengthen backlog reseeding and empty-loop prevention rules.",
            next_recommendation="rerun autonomy after tightening loop health rules",
            commands=[
                SELF_INSPECT_COMMAND,
                AUTONOMY_ONE_LOOP_COMMAND,
                AUTONOMY_STATUS_JSON_COMMAND,
            ],
            context_paths=merge_context_paths(
                task_context_paths(task),
                recommendation_context_paths(recommendation),
                loop_local_self_inspection_context_paths(root, loop_id),
            ),
        )
    if "executor_dry_run_blocked" in signals:
        return prepared_action(
            task_id=task_id,
            action_type="executor_safety_review_plan",
            title="Review blocked executor dry-run safety evidence.",
            next_recommendation=(
                "resolve blocked dry-run safety findings and rerun self-inspection"
            ),
            commands=[
                executor_dry_run_command(session_id),
                SELF_INSPECT_COMMAND,
            ],
        )
    if "executor_dry_run_attention" in signals:
        return prepared_action(
            task_id=task_id,
            action_type="executor_safety_followup_plan",
            title="Review dry-run attention signals before another executor retry.",
            next_recommendation=(
                "review dry-run attention signals and rerun self-inspection"
            ),
            commands=[
                executor_dry_run_command(session_id),
                SELF_INSPECT_COMMAND,
            ],
        )
    if category in {
        "workflow_gap",
        "integration_gap",
        "provenance_gap",
        "partial_completion_gap",
        "no_op_safeguard_gap",
    }:
        if recommendation == "audit_worktree_integration":
            return workflow_gap_action(
                root=root,
                loop_id=loop_id,
                task_id=task_id,
                task=task,
                recommendation=recommendation,
            )
        return prepared_action(
            task_id=task_id,
            action_type="workflow_gap_plan",
            title="Prepare a deterministic remediation plan for the workflow gap.",
            next_recommendation="close the structural gap and rerun self-inspection",
            commands=[SELF_INSPECT_COMMAND],
        )
    if category in {
        "worktree_risk",
        "commit_isolation_gap",
        "artifact_hygiene_gap",
        "runtime_artifact_cleanup_gap",
        "deferred_cleanup_gap",
        "evidence_freshness_gap",
    }:
        return cleanup_action(
            root=root,
            loop_id=loop_id,
            task_id=task_id,
            task=task,
            recommendation=recommendation,
        )
    if category == "artifact_consistency":
        return prepared_action(
            task_id=task_id,
            action_type="artifact_consistency_plan",
            title="Restore missing companion artifacts for the recorded workflow.",
            next_recommendation="rerun the command that owns the missing artifacts",
            commands=[
                "python -m qa_z verify --baseline-run <run> --candidate-run <run>"
            ],
        )
    if category == "session_gap":
        action = prepared_action(
            task_id=task_id,
            action_type="repair_session_followup",
            title="Resume or verify the existing repair session.",
            next_recommendation="continue the existing repair-session workflow",
            commands=[
                "python -m qa_z repair-session status --session "
                f"{session_id or '<session>'}"
            ],
        )
        action["session_id"] = session_id
        return action
    if category in {"verify_regression", "verification_failure"} or recommendation == (
        "stabilize_verification_surface"
    ):
        baseline_run = baseline_run_from_verify_evidence(root, task)
        if config is not None and baseline_run:
            return repair_session_action(
                root=root,
                config=config,
                loop_id=loop_id,
                task_id=task_id,
                baseline_run=baseline_run,
                context_paths=merge_context_paths(
                    task_context_paths(task),
                    loop_local_self_inspection_context_paths(root, loop_id),
                ),
                deps=deps,
            )
        action = prepared_action(
            task_id=task_id,
            action_type="verification_stabilization_plan",
            title="Create a stabilization plan from verification evidence.",
            next_recommendation="prepare a repair session once baseline evidence is available",
            commands=[
                "python -m qa_z verify --baseline-run <baseline> --candidate-run <candidate>"
            ],
        )
        action["baseline_run"] = baseline_run
        return action
    return prepared_action(
        task_id=task_id,
        action_type="implementation_plan",
        title="Prepare an implementation plan for the selected backlog item.",
        next_recommendation="turn selected evidence into a scoped repair plan",
        commands=[SELF_INSPECT_COMMAND],
    )
