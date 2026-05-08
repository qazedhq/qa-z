"""Recommendation-aware cleanup action helpers for autonomy."""

from __future__ import annotations

from pathlib import Path

from qa_z.autonomy_action_context import (
    loop_local_self_inspection_context_paths,
    merge_context_paths,
    recommendation_context_paths,
    task_context_paths,
)
from qa_z.autonomy_action_packets import prepared_action
from qa_z.operator_commands import BACKLOG_REFRESH_JSON_COMMAND
from qa_z.operator_commands import RUNTIME_ARTIFACT_CLEANUP_APPLY_COMMAND
from qa_z.operator_commands import RUNTIME_ARTIFACT_CLEANUP_COMMAND
from qa_z.operator_commands import SELF_INSPECT_JSON_COMMAND
from qa_z.operator_commands import STRICT_WORKTREE_COMMIT_PLAN_COMMAND

__all__ = ["cleanup_action", "workflow_gap_action"]


def cleanup_action(
    *,
    root: Path,
    loop_id: str,
    task_id: str,
    task: dict[str, object],
    recommendation: str,
) -> dict[str, object]:
    """Build a recommendation-aware cleanup action packet."""
    default_next = "reduce integration risk and rerun self-inspection"
    cleanup_review_command = RUNTIME_ARTIFACT_CLEANUP_COMMAND
    cleanup_apply_command = RUNTIME_ARTIFACT_CLEANUP_APPLY_COMMAND
    worktree_plan_command = STRICT_WORKTREE_COMMIT_PLAN_COMMAND
    category = str(task.get("category") or "")
    titles = {
        "isolate_foundation_commit": "Prepare a deterministic commit-isolation plan.",
        "reduce_integration_risk": (
            "Prepare a deterministic cleanup and integration-risk reduction plan."
        ),
        "separate_runtime_from_source_artifacts": (
            "Prepare a deterministic runtime-artifact cleanup plan."
        ),
        "clarify_generated_vs_frozen_evidence_policy": (
            "Prepare a deterministic generated-versus-frozen evidence policy review."
        ),
        "triage_and_isolate_changes": (
            "Prepare a deterministic worktree triage and isolation plan."
        ),
    }
    if category == "runtime_artifact_cleanup_gap":
        titles["triage_and_isolate_changes"] = (
            "Prepare a deterministic runtime-artifact cleanup follow-through plan."
        )
    next_steps = {
        "isolate_foundation_commit": (
            "isolate the foundation commit before rerunning self-inspection"
        ),
        "reduce_integration_risk": (
            "reduce dirty worktree integration risk and rerun self-inspection"
        ),
        "separate_runtime_from_source_artifacts": (
            "separate runtime outputs from source changes and rerun self-inspection"
        ),
        "clarify_generated_vs_frozen_evidence_policy": (
            "clarify generated versus frozen benchmark evidence policy and rerun "
            "self-inspection"
        ),
        "triage_and_isolate_changes": (
            "triage and isolate worktree changes before rerunning self-inspection"
        ),
    }
    if category == "runtime_artifact_cleanup_gap":
        next_steps["triage_and_isolate_changes"] = (
            "clear policy-managed runtime artifacts before rerunning self-inspection"
        )
    commands = ["git status --short"]
    if recommendation in {
        "reduce_integration_risk",
        "separate_runtime_from_source_artifacts",
        "clarify_generated_vs_frozen_evidence_policy",
        "triage_and_isolate_changes",
    }:
        commands.append(cleanup_review_command)
    if recommendation == "reduce_integration_risk":
        commands.append(worktree_plan_command)
        commands.extend(patch_add_commands_from_task_evidence(task))
    if recommendation in {
        "reduce_integration_risk",
        "triage_and_isolate_changes",
    }:
        if category == "runtime_artifact_cleanup_gap":
            commands.append(cleanup_apply_command)
        else:
            commands.append(BACKLOG_REFRESH_JSON_COMMAND)
    if recommendation == "separate_runtime_from_source_artifacts":
        commands.append(cleanup_apply_command)
    commands.append(SELF_INSPECT_JSON_COMMAND)
    return prepared_action(
        task_id=task_id,
        action_type="integration_cleanup_plan",
        title=titles.get(
            recommendation,
            "Prepare a deterministic cleanup and integration-risk reduction plan.",
        ),
        next_recommendation=next_steps.get(
            recommendation,
            recommendation.replace("_", " ") if recommendation else default_next,
        ),
        commands=commands,
        context_paths=merge_context_paths(
            loop_local_self_inspection_context_paths(root, loop_id),
            task_context_paths(task),
            recommendation_context_paths(recommendation),
        ),
    )


def patch_add_commands_from_task_evidence(task: dict[str, object]) -> list[str]:
    """Return scoped patch-add commands carried by strict worktree evidence."""
    evidence = task.get("evidence")
    if not isinstance(evidence, list):
        return []
    commands: list[str] = []
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("source") or "").strip() != "worktree_commit_plan_json":
            continue
        patch_commands = entry.get("patch_command_texts")
        if not isinstance(patch_commands, list):
            continue
        commands.extend(
            str(command).strip()
            for command in patch_commands
            if isinstance(command, str) and command.strip()
        )
    return commands


def workflow_gap_action(
    *,
    root: Path,
    loop_id: str,
    task_id: str,
    task: dict[str, object],
    recommendation: str,
) -> dict[str, object]:
    """Build a recommendation-aware workflow-gap action packet."""
    next_steps = {
        "audit_worktree_integration": (
            "audit worktree integration evidence and rerun self-inspection"
        ),
    }
    return prepared_action(
        task_id=task_id,
        action_type="workflow_gap_plan",
        title="Prepare a deterministic remediation plan for the workflow gap.",
        next_recommendation=next_steps.get(
            recommendation,
            "close the structural gap and rerun self-inspection",
        ),
        commands=[
            "git status --short",
            BACKLOG_REFRESH_JSON_COMMAND,
            SELF_INSPECT_JSON_COMMAND,
        ],
        context_paths=merge_context_paths(
            loop_local_self_inspection_context_paths(root, loop_id),
            task_context_paths(task),
            recommendation_context_paths(recommendation),
        ),
    )
