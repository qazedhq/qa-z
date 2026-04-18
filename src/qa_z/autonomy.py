"""Deterministic autonomy workflow loops for QA-Z planning."""

from __future__ import annotations

import json
import math
import re
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from qa_z.artifacts import ArtifactLoadError, format_path
from qa_z.repair_session import create_repair_session
from qa_z.self_improvement import (
    SELF_IMPROVEMENT_SCHEMA_VERSION,
    compact_backlog_evidence_summary,
    evidence_paths,
    fallback_family_for_category,
    fallback_families_for_items,
    int_value,
    load_backlog,
    open_backlog_items,
    run_self_inspection,
    select_next_tasks,
    slugify,
)

AUTONOMY_SUMMARY_KIND = "qa_z.autonomy_summary"
AUTONOMY_OUTCOME_KIND = "qa_z.autonomy_outcome"
AUTONOMY_STATUS_KIND = "qa_z.autonomy_status"

OPEN_SESSION_STATES = {
    "created",
    "handoff_ready",
    "waiting_for_external_repair",
    "candidate_generated",
    "verification_complete",
    "failed",
}
MAX_CONSECUTIVE_BLOCKED_LOOPS = 2


def run_autonomy(
    *,
    root: Path,
    config: dict[str, Any] | None = None,
    loops: int = 1,
    count: int = 3,
    now: str | None = None,
    min_runtime_seconds: int | float = 0,
    min_loop_seconds: int | float = 0,
    monotonic: Callable[[], float] | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    """Run deterministic self-improvement planning loops."""
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    generated_at = now or utc_now()
    loops_requested = max(1, int(loops))
    runtime_target_seconds = coerce_duration_seconds(min_runtime_seconds)
    minimum_loop_seconds = coerce_duration_seconds(min_loop_seconds)
    monotonic_fn = monotonic or time.monotonic
    sleep_fn = sleeper or time.sleep
    run_started_at = now or utc_now()
    run_started_monotonic = monotonic_fn()
    outcomes: list[dict[str, Any]] = []
    consecutive_blocked_loops = 0
    stop_reason = "requested_loops_and_runtime_met"
    loop_index = 1
    while True:
        loop_generated_at = now or utc_now()
        loop_started_monotonic = monotonic_fn()
        outcome = run_autonomy_loop(
            root=root,
            config=config,
            loop_id=autonomy_loop_id(generated_at, loop_index),
            generated_at=loop_generated_at,
            count=count,
        )
        loop_elapsed = max(0.0, monotonic_fn() - loop_started_monotonic)
        remaining_loop_time = max(0.0, minimum_loop_seconds - loop_elapsed)
        if remaining_loop_time > 0:
            sleep_fn(remaining_loop_time)
        cumulative_elapsed = max(0.0, monotonic_fn() - run_started_monotonic)
        runtime_budget_met = cumulative_elapsed >= runtime_target_seconds
        enriched_outcome = with_runtime_fields(
            outcome=outcome,
            loop_started_at=loop_generated_at,
            loop_finished_at=now or utc_now(),
            loop_elapsed_seconds=coerce_duration_seconds(
                max(0.0, monotonic_fn() - loop_started_monotonic)
            ),
            cumulative_elapsed_seconds=coerce_duration_seconds(cumulative_elapsed),
            runtime_target_seconds=runtime_target_seconds,
            min_loop_seconds=minimum_loop_seconds,
            runtime_budget_met=runtime_budget_met,
        )
        write_outcome_artifact(root, enriched_outcome)
        update_history_entry(
            root / ".qa-z" / "loops" / "history.jsonl",
            loop_id=str(enriched_outcome["loop_id"]),
            outcome=enriched_outcome,
        )
        outcomes.append(enriched_outcome)
        if enriched_outcome.get("state") == "blocked_no_candidates":
            consecutive_blocked_loops += 1
        else:
            consecutive_blocked_loops = 0
        if len(outcomes) >= loops_requested and runtime_budget_met:
            stop_reason = "requested_loops_and_runtime_met"
            break
        if consecutive_blocked_loops >= MAX_CONSECUTIVE_BLOCKED_LOOPS:
            stop_reason = "repeated_blocked_no_candidates"
            break
        loop_index += 1

    runtime_elapsed_seconds = coerce_duration_seconds(
        max(0.0, monotonic_fn() - run_started_monotonic)
    )
    created_session_ids = [
        session_id
        for outcome in outcomes
        for session_id in outcome.get("created_session_ids", [])
    ]
    summary = {
        "kind": AUTONOMY_SUMMARY_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "run_started_at": run_started_at,
        "finished_at": now or utc_now(),
        "loops_requested": loops_requested,
        "loops_completed": len(outcomes),
        "latest_loop_id": outcomes[-1]["loop_id"] if outcomes else None,
        "runtime_target_seconds": runtime_target_seconds,
        "runtime_elapsed_seconds": runtime_elapsed_seconds,
        "runtime_remaining_seconds": max(
            runtime_target_seconds - runtime_elapsed_seconds, 0
        ),
        "runtime_budget_met": runtime_elapsed_seconds >= runtime_target_seconds,
        "min_loop_seconds": minimum_loop_seconds,
        "stop_reason": stop_reason,
        "consecutive_blocked_loops": consecutive_blocked_loops,
        "created_session_ids": created_session_ids,
        "outcomes": outcomes,
    }
    latest_dir = loops_root(root) / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    write_json(latest_dir / "autonomy_summary.json", summary)
    return summary


def run_autonomy_loop(
    *,
    root: Path,
    config: dict[str, Any] | None,
    loop_id: str,
    generated_at: str,
    count: int,
) -> dict[str, Any]:
    """Run one inspect/select/plan/record autonomy loop."""
    transitions = ["inspected"]
    backlog_before = load_backlog(root)
    backlog_open_count_before_inspection = len(open_backlog_items(backlog_before))
    empty_backlog_detected = backlog_open_count_before_inspection == 0
    inspection_paths = run_self_inspection(root=root, now=generated_at, loop_id=loop_id)
    backlog_after = load_backlog(root)
    backlog_open_count_after_inspection = len(open_backlog_items(backlog_after))
    selection_paths = select_next_tasks(
        root=root, count=count, now=generated_at, loop_id=loop_id
    )
    transitions.append("selected")

    selected_artifact = read_json_object(selection_paths.selected_tasks_path)
    selected_tasks = [
        item
        for item in selected_artifact.get("selected_tasks", [])
        if isinstance(item, dict)
    ]
    fallback_selected = empty_backlog_detected and any(
        is_fallback_selection_task(task) for task in selected_tasks
    )
    if empty_backlog_detected and (fallback_selected or not selected_tasks):
        transitions.append("empty_backlog_detected")
    if fallback_selected:
        transitions.extend(["reseeded", "fallback_selected"])
    elif not selected_tasks:
        transitions.append("blocked_no_candidates")
    selection_gap_reason = None
    if not selected_tasks and not fallback_selected:
        selection_gap_reason = selection_gap_reason_for_loop(
            backlog_open_count_after_inspection=backlog_open_count_after_inspection
        )
    observed_verification = verification_observations(root, selected_tasks)
    if observed_verification:
        transitions.append("verification_observed")
    actions = [
        action_for_task(root=root, config=config, loop_id=loop_id, task=task)
        for task in selected_tasks
    ]
    created_session_ids = [
        str(action["session_id"])
        for action in actions
        if action.get("type") == "repair_session" and action.get("session_id")
    ]
    if created_session_ids:
        transitions.append("session_prepared")
    if selected_tasks:
        transitions.append("awaiting_repair")

    loop_dir = loops_root(root) / loop_id
    latest_dir = loops_root(root) / "latest"
    loop_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    copy_artifact(inspection_paths.self_inspection_path, loop_dir / "self_inspect.json")
    copy_artifact(selection_paths.selected_tasks_path, loop_dir / "selected_tasks.json")
    selected_task_ids = [str(task.get("id")) for task in selected_tasks]
    selected_fallback_families = fallback_families_for_items(selected_tasks)
    transitions.extend(["recorded", "completed"])
    state = "completed"
    if fallback_selected:
        state = "fallback_selected"
    elif not selected_tasks:
        state = "blocked_no_candidates"
    loop_health = build_loop_health(
        selected_count=len(selected_tasks),
        fallback_selected=fallback_selected,
        selection_gap_reason=selection_gap_reason,
        backlog_open_count_before_inspection=backlog_open_count_before_inspection,
        backlog_open_count_after_inspection=backlog_open_count_after_inspection,
    )
    plan_text = render_autonomy_loop_plan(
        loop_id=loop_id,
        generated_at=generated_at,
        selected_tasks=selected_tasks,
        actions=actions,
        selected_fallback_families=selected_fallback_families,
        selection_gap_reason=selection_gap_reason,
        backlog_open_count_before_inspection=backlog_open_count_before_inspection,
        backlog_open_count_after_inspection=backlog_open_count_after_inspection,
        loop_health=loop_health,
    )
    (loop_dir / "loop_plan.md").write_text(plan_text, encoding="utf-8")
    (latest_dir / "loop_plan.md").write_text(plan_text, encoding="utf-8")
    outcome = {
        "kind": AUTONOMY_OUTCOME_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "loop_id": loop_id,
        "generated_at": generated_at,
        "state": state,
        "state_transitions": transitions,
        "selected_task_ids": selected_task_ids,
        "selected_fallback_families": selected_fallback_families,
        "backlog_open_count_before_inspection": backlog_open_count_before_inspection,
        "backlog_open_count_after_inspection": backlog_open_count_after_inspection,
        "loop_health": loop_health,
        "evidence_used": evidence_paths(selected_tasks),
        "verification_evidence": observed_verification,
        "actions_prepared": actions,
        "created_session_ids": created_session_ids,
        "next_recommendations": next_recommendations(
            selected_tasks,
            actions,
            state=state,
            selection_gap_reason=selection_gap_reason,
        ),
        "artifacts": {
            "self_inspection": format_path(loop_dir / "self_inspect.json", root),
            "selected_tasks": format_path(loop_dir / "selected_tasks.json", root),
            "loop_plan": format_path(loop_dir / "loop_plan.md", root),
            "outcome": format_path(loop_dir / "outcome.json", root),
        },
    }
    if selection_gap_reason:
        outcome["selection_gap_reason"] = selection_gap_reason
    write_json(loop_dir / "outcome.json", outcome)
    copy_artifact(loop_dir / "self_inspect.json", latest_dir / "self_inspect.json")
    copy_artifact(loop_dir / "selected_tasks.json", latest_dir / "selected_tasks.json")
    copy_artifact(loop_dir / "outcome.json", latest_dir / "outcome.json")
    update_history_entry(selection_paths.history_path, loop_id=loop_id, outcome=outcome)
    return outcome


def action_for_task(
    *,
    root: Path,
    config: dict[str, Any] | None,
    loop_id: str,
    task: dict[str, Any],
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
            commands=["python -m qa_z benchmark"],
        )
    if category == "policy_gap":
        return prepared_action(
            task_id=task_id,
            action_type="policy_fixture_plan",
            title="Add a deterministic policy fixture or policy expectation.",
            next_recommendation="rerun policy-focused benchmark fixtures",
            commands=["python -m qa_z benchmark"],
        )
    if category in {"docs_drift", "schema_drift"}:
        return prepared_action(
            task_id=task_id,
            action_type="docs_sync_plan",
            title="Synchronize README, schema docs, and examples with artifacts.",
            next_recommendation="rerun self-inspection after docs sync",
            commands=["python -m qa_z self-inspect"],
        )
    if category in {"backlog_reseeding_gap", "autonomy_selection_gap"}:
        return prepared_action(
            task_id=task_id,
            action_type="loop_health_plan",
            title="Strengthen backlog reseeding and empty-loop prevention rules.",
            next_recommendation="rerun autonomy after tightening loop health rules",
            commands=[
                "python -m qa_z self-inspect",
                "python -m qa_z autonomy --loops 1",
            ],
            context_paths=task_context_paths(task),
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
                "python -m qa_z self-inspect",
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
                "python -m qa_z self-inspect",
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
                task_id=task_id,
                task=task,
                recommendation=recommendation,
            )
        return prepared_action(
            task_id=task_id,
            action_type="workflow_gap_plan",
            title="Prepare a deterministic remediation plan for the workflow gap.",
            next_recommendation="close the structural gap and rerun self-inspection",
            commands=["python -m qa_z self-inspect"],
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
        session_id = existing_session_id(task)
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
    if category == "verify_regression" or recommendation == (
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
                context_paths=task_context_paths(task),
            )
        action = prepared_action(
            task_id=task_id,
            action_type="verification_stabilization_plan",
            title="Create a stabilization plan from verification regression evidence.",
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
        commands=["python -m qa_z self-inspect"],
    )


def repair_session_action(
    *,
    root: Path,
    config: dict[str, Any],
    loop_id: str,
    task_id: str,
    baseline_run: str,
    context_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Prepare a repair session for a task when baseline evidence is available."""
    session_id = f"{loop_id}-{slugify(task_id)}"
    try:
        result = create_repair_session(
            root=root,
            config=config,
            baseline_run=baseline_run,
            session_id=session_id,
        )
    except (ArtifactLoadError, FileNotFoundError, ValueError) as exc:
        action = prepared_action(
            task_id=task_id,
            action_type="verification_stabilization_plan",
            title="Repair session could not be created from current evidence.",
            next_recommendation="repair baseline evidence before starting a session",
            commands=[
                f"python -m qa_z repair-session start --baseline-run {baseline_run}"
            ],
            context_paths=context_paths,
        )
        action["baseline_run"] = baseline_run
        action["error"] = str(exc)
        return action

    session = result.session
    action = {
        "type": "repair_session",
        "task_id": task_id,
        "title": "Prepared a local repair session from verification evidence.",
        "baseline_run": baseline_run,
        "session_id": session.session_id,
        "session_dir": session.session_dir,
        "executor_guide": session.executor_guide_path,
        "handoff_dir": session.handoff_dir,
        "next_recommendation": "run external repair, then repair-session verify",
        "commands": [
            f"python -m qa_z repair-session status --session {session.session_dir}",
            f"python -m qa_z repair-session verify --session {session.session_dir} --rerun",
        ],
    }
    if context_paths:
        action["context_paths"] = list(context_paths)
    return action


def prepared_action(
    *,
    task_id: str,
    action_type: str,
    title: str,
    next_recommendation: str,
    commands: list[str],
    context_paths: list[str] | None = None,
) -> dict[str, Any]:
    """Build a stable non-executing prepared action."""
    action = {
        "type": action_type,
        "task_id": task_id,
        "title": title,
        "commands": commands,
        "next_recommendation": next_recommendation,
    }
    if context_paths:
        action["context_paths"] = list(context_paths)
    return action


def cleanup_action(
    *, task_id: str, task: dict[str, Any], recommendation: str
) -> dict[str, Any]:
    """Build a recommendation-aware cleanup action packet."""
    default_next = "reduce integration risk and rerun self-inspection"
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
        commands=[
            "git status --short",
            "python -m qa_z backlog --json",
            "python -m qa_z self-inspect --json",
        ],
        context_paths=merge_context_paths(
            task_context_paths(task),
            recommendation_context_paths(recommendation),
        ),
    )


def workflow_gap_action(
    *, task_id: str, task: dict[str, Any], recommendation: str
) -> dict[str, Any]:
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
            "python -m qa_z backlog --json",
            "python -m qa_z self-inspect --json",
        ],
        context_paths=merge_context_paths(
            task_context_paths(task),
            recommendation_context_paths(recommendation),
        ),
    )


def task_context_paths(task: dict[str, Any]) -> list[str]:
    """Return unique non-root evidence paths from a selected task."""
    return merge_context_paths(
        [
            str(entry.get("path") or "").strip()
            for entry in task.get("evidence", [])
            if isinstance(entry, dict)
            and str(entry.get("path") or "").strip()
            and str(entry.get("path") or "").strip() != "."
        ]
    )


def recommendation_context_paths(recommendation: str) -> list[str]:
    """Return default report context for known recommendations."""
    by_recommendation = {
        "audit_worktree_integration": [
            "docs/reports/current-state-analysis.md",
            "docs/reports/worktree-triage.md",
            "docs/reports/worktree-commit-plan.md",
        ],
        "reduce_integration_risk": ["docs/reports/worktree-triage.md"],
        "isolate_foundation_commit": ["docs/reports/worktree-commit-plan.md"],
        "separate_runtime_from_source_artifacts": ["docs/reports/worktree-triage.md"],
        "clarify_generated_vs_frozen_evidence_policy": [
            "docs/generated-vs-frozen-evidence-policy.md",
            "docs/reports/worktree-triage.md",
            "docs/reports/current-state-analysis.md",
        ],
        "triage_and_isolate_changes": [
            "docs/generated-vs-frozen-evidence-policy.md",
            "docs/reports/worktree-triage.md",
            "docs/reports/worktree-commit-plan.md",
        ],
    }
    return by_recommendation.get(recommendation, [])


def merge_context_paths(*groups: list[str]) -> list[str]:
    """Return stable sorted unique context paths."""
    merged = {
        path.strip()
        for group in groups
        for path in group
        if isinstance(path, str) and path.strip()
    }
    return sorted(merged)


def is_fallback_selection_task(task: dict[str, Any]) -> bool:
    """Return whether a selected task came from fallback backlog reseeding."""
    category = str(task.get("category") or "")
    return fallback_family_for_category(category) is not None


def build_loop_health(
    *,
    selected_count: int,
    fallback_selected: bool,
    selection_gap_reason: str | None,
    backlog_open_count_before_inspection: int,
    backlog_open_count_after_inspection: int,
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
        "summary": loop_health_summary_text(
            classification=classification,
            selected_count=selected_count,
            fallback_selected=fallback_selected,
            stale_open_items_closed=stale_open_items_closed,
            backlog_open_count_before_inspection=backlog_open_count_before_inspection,
            backlog_open_count_after_inspection=backlog_open_count_after_inspection,
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
) -> str:
    """Render one deterministic loop-health summary sentence."""
    if classification == "taskless":
        if stale_open_items_closed:
            suffix = "item" if stale_open_items_closed == 1 else "items"
            return (
                f"self-inspection closed {stale_open_items_closed} stale open "
                f"backlog {suffix}; no replacement fallback candidates were selected"
            )
        if backlog_open_count_before_inspection <= 0:
            return (
                "no open backlog items before inspection and no fallback candidates "
                "were generated"
            )
        if backlog_open_count_after_inspection > 0:
            return "open backlog items remained but selection produced no task"
        return "no evidence-backed backlog items survived inspection"
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
    lines.extend(["", "## Selected Tasks", ""])
    if not selected_tasks:
        lines.append("- No open backlog tasks were selected.")
        if loop_health:
            lines.append(
                f"- Loop health: `{loop_health.get('classification', 'unknown')}`"
            )
            if loop_health.get("summary"):
                lines.append(f"- Loop health summary: {loop_health['summary']}")
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


def load_autonomy_status(root: Path) -> dict[str, Any]:
    """Load a compact status view of the latest autonomy artifacts."""
    root = root.resolve()
    latest_dir = loops_root(root) / "latest"
    summary = read_json_object(latest_dir / "autonomy_summary.json")
    outcome = read_json_object(latest_dir / "outcome.json")
    selected = read_json_object(latest_dir / "selected_tasks.json")
    selected_tasks = [
        item
        for item in selected.get("selected_tasks", [])
        if isinstance(item, dict) and item.get("id")
    ]
    open_sessions = current_open_sessions(root)
    backlog_items = backlog_top_items(root)
    recent_verify = latest_verify_observation(root)
    prepared_actions = status_prepared_actions(outcome.get("actions_prepared"))
    next_actions = [
        str(item)
        for item in outcome.get("next_recommendations", [])
        if isinstance(item, str) and item.strip()
    ]
    return {
        "kind": AUTONOMY_STATUS_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "latest_loop_id": outcome.get("loop_id"),
        "latest_state": outcome.get("state"),
        "latest_selected_tasks": [str(item["id"]) for item in selected_tasks],
        "latest_selected_fallback_families": [
            str(item)
            for item in outcome.get("selected_fallback_families", [])
            if isinstance(item, str) and item.strip()
        ],
        "latest_selected_task_details": status_selected_task_details(selected_tasks),
        "latest_prepared_actions": prepared_actions,
        "latest_next_recommendations": next_actions,
        "latest_loop_health": outcome.get("loop_health") or {},
        "latest_selection_gap_reason": outcome.get("selection_gap_reason"),
        "latest_backlog_open_count_before_inspection": int_value(
            outcome.get("backlog_open_count_before_inspection")
        ),
        "latest_backlog_open_count_after_inspection": int_value(
            outcome.get("backlog_open_count_after_inspection")
        ),
        "loops_completed": int_value(summary.get("loops_completed")),
        "runtime_target_seconds": int_value(summary.get("runtime_target_seconds")),
        "runtime_elapsed_seconds": int_value(summary.get("runtime_elapsed_seconds")),
        "runtime_remaining_seconds": int_value(
            summary.get("runtime_remaining_seconds")
        ),
        "runtime_budget_met": bool(summary.get("runtime_budget_met")),
        "min_loop_seconds": int_value(summary.get("min_loop_seconds")),
        "latest_loop_elapsed_seconds": int_value(outcome.get("loop_elapsed_seconds")),
        "open_session_count": len(open_sessions),
        "open_sessions": open_sessions,
        "recent_verify_verdict": recent_verify,
        "backlog_top_items": backlog_items,
    }


def render_autonomy_summary(summary: dict[str, Any], root: Path) -> str:
    """Render human stdout for an autonomy run."""
    latest_loop_id = summary.get("latest_loop_id") or "none"
    latest_outcome = (loops_root(root) / "latest" / "outcome.json").resolve()
    return "\n".join(
        [
            "qa-z autonomy: completed planning loops",
            f"Loops requested: {summary.get('loops_requested', 0)}",
            f"Loops completed: {summary.get('loops_completed', 0)}",
            f"Latest loop: {latest_loop_id}",
            "Runtime: "
            + format_runtime_progress(
                elapsed_seconds=int_value(summary.get("runtime_elapsed_seconds")),
                target_seconds=int_value(summary.get("runtime_target_seconds")),
            ),
            f"Min loop seconds: {summary.get('min_loop_seconds', 0)}",
            f"Outcome: {format_path(latest_outcome, root)}",
            f"Created sessions: {len(summary.get('created_session_ids', []))}",
        ]
    )


def render_autonomy_status(status: dict[str, Any]) -> str:
    """Render human stdout for autonomy status."""
    selected = status.get("latest_selected_tasks") or []
    selected_fallback_families = [
        str(item)
        for item in status.get("latest_selected_fallback_families", [])
        if isinstance(item, str) and item.strip()
    ]
    selected_details = status.get("latest_selected_task_details") or []
    prepared_actions = status.get("latest_prepared_actions") or []
    next_steps = status.get("latest_next_recommendations") or []
    top_items = status.get("backlog_top_items") or []
    loop_health = (
        status.get("latest_loop_health")
        if isinstance(status.get("latest_loop_health"), dict)
        else {}
    )
    lines = [
        f"qa-z autonomy status: {status.get('latest_state') or 'no loops recorded'}",
        f"Latest loop: {status.get('latest_loop_id') or 'none'}",
        "Selected tasks: " + (", ".join(selected) if selected else "none"),
        "Runtime: "
        + format_runtime_progress(
            elapsed_seconds=int_value(status.get("runtime_elapsed_seconds")),
            target_seconds=int_value(status.get("runtime_target_seconds")),
        ),
        f"Runtime budget met: {status.get('runtime_budget_met', False)}",
        f"Min loop seconds: {status.get('min_loop_seconds', 0)}",
        f"Open sessions: {status.get('open_session_count', 0)}",
        f"Recent verify verdict: {status.get('recent_verify_verdict') or 'none'}",
        "Selected task details:",
    ]
    if selected_fallback_families:
        lines.append(
            "Selected fallback families: " + ", ".join(selected_fallback_families)
        )
    if loop_health:
        lines.append(f"Loop health: {loop_health.get('classification') or 'unknown'}")
        if loop_health.get("summary"):
            lines.append(f"Loop health summary: {loop_health['summary']}")
    if status.get("latest_selection_gap_reason"):
        lines.append(
            f"Selection gap reason: {status.get('latest_selection_gap_reason')}"
        )
        lines.append(
            "Open backlog count: "
            f"{int_value(status.get('latest_backlog_open_count_before_inspection'))} "
            "before inspection, "
            f"{int_value(status.get('latest_backlog_open_count_after_inspection'))} "
            "after inspection"
        )
    if not selected_details:
        lines.append("- none")
    for item in selected_details:
        lines.append(
            f"- {item.get('id')}: {item.get('title', item.get('id', 'untitled'))}"
        )
        if item.get("recommendation"):
            lines.append(f"  recommendation: {item['recommendation']}")
        if item.get("selection_priority_score") is not None:
            lines.append(f"  selection score: {item['selection_priority_score']}")
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
        if item.get("evidence_summary"):
            lines.append(f"  evidence: {item['evidence_summary']}")
    lines.extend(
        [
            "Prepared actions:",
        ]
    )
    open_sessions = status.get("open_sessions") or []
    if open_sessions:
        lines.append("Open session details:")
        for session in open_sessions:
            lines.append(
                "- "
                f"{session.get('session_id')}: {session.get('state')} "
                f"({session.get('session_dir')})"
            )
    if not prepared_actions:
        lines.append("- none")
    for action in prepared_actions:
        action_type = action.get("type") or "unknown"
        task_id = action.get("task_id") or "unknown"
        lines.append(f"- {action_type} for {task_id}")
        if action.get("next_recommendation"):
            lines.append(f"  next: {action['next_recommendation']}")
        commands = action.get("commands")
        if isinstance(commands, list) and commands:
            lines.append(f"  commands: {'; '.join(str(item) for item in commands)}")
        context_paths = action.get("context_paths")
        if isinstance(context_paths, list) and context_paths:
            lines.append(f"  context: {', '.join(str(item) for item in context_paths)}")
    lines.extend(
        [
            "Next recommendations:",
        ]
    )
    if not next_steps:
        lines.append("- none")
    for recommendation in next_steps:
        lines.append(f"- {recommendation}")
    lines.extend(
        [
            "Backlog top items:",
        ]
    )
    if not top_items:
        lines.append("- none")
    for item in top_items:
        lines.append(
            f"- {item.get('id')}: priority {item.get('priority_score')} "
            f"({item.get('category')})"
        )
        if item.get("title"):
            lines.append(f"  title: {item['title']}")
        if item.get("recommendation"):
            lines.append(f"  next: {item['recommendation']}")
        if item.get("evidence_summary"):
            lines.append(f"  evidence: {item['evidence_summary']}")
    return "\n".join(lines)


def format_runtime_progress(*, elapsed_seconds: int, target_seconds: int) -> str:
    """Render runtime progress without the confusing elapsed/0 form."""
    if target_seconds <= 0:
        return f"{elapsed_seconds} seconds elapsed (no minimum budget)"
    return f"{elapsed_seconds}/{target_seconds} seconds"


def next_recommendations(
    selected_tasks: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    *,
    state: str = "completed",
    selection_gap_reason: str | None = None,
) -> list[str]:
    """Return compact next recommendations from prepared actions."""
    if not selected_tasks:
        if state == "blocked_no_candidates":
            if selection_gap_reason == "no_open_backlog_after_inspection":
                return ["no evidence-backed fallback candidates available"]
            return ["review selection inputs and rerun self-inspection"]
        return ["no open backlog tasks selected"]
    recommendations = [
        str(action["next_recommendation"])
        for action in actions
        if action.get("next_recommendation")
    ]
    return recommendations or ["prepare selected task evidence for external repair"]


def status_prepared_actions(actions: object) -> list[dict[str, Any]]:
    """Return compact prepared actions for autonomy status output."""
    if not isinstance(actions, list):
        return []
    prepared: list[dict[str, Any]] = []
    for action in actions:
        if not isinstance(action, dict) or not action.get("type"):
            continue
        compact: dict[str, Any] = {
            "type": str(action.get("type")),
            "task_id": str(action.get("task_id") or "unknown"),
        }
        if action.get("title"):
            compact["title"] = str(action["title"])
        if action.get("next_recommendation"):
            compact["next_recommendation"] = str(action["next_recommendation"])
        commands = [
            str(item)
            for item in action.get("commands", [])
            if isinstance(item, str) and item.strip()
        ]
        if commands:
            compact["commands"] = commands
        context_paths = [
            str(item)
            for item in action.get("context_paths", [])
            if isinstance(item, str) and item.strip()
        ]
        if context_paths:
            compact["context_paths"] = context_paths
        if action.get("session_id"):
            compact["session_id"] = str(action["session_id"])
        if action.get("baseline_run"):
            compact["baseline_run"] = str(action["baseline_run"])
        prepared.append(compact)
    return prepared


def status_selected_task_details(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return compact selected-task details for autonomy status output."""
    details: list[dict[str, Any]] = []
    for item in items:
        detail: dict[str, Any] = {
            "id": str(item.get("id") or "unknown"),
            "title": str(item.get("title") or item.get("id") or "untitled"),
            "category": str(item.get("category") or ""),
            "recommendation": str(item.get("recommendation") or ""),
            "evidence_summary": compact_backlog_evidence_summary(item),
        }
        if item.get("selection_priority_score") is not None:
            detail["selection_priority_score"] = int_value(
                item.get("selection_priority_score")
            )
        if item.get("selection_penalty") is not None:
            detail["selection_penalty"] = int_value(item.get("selection_penalty"))
        selection_penalty_reasons = [
            str(reason)
            for reason in item.get("selection_penalty_reasons", [])
            if isinstance(reason, str) and reason.strip()
        ]
        if selection_penalty_reasons:
            detail["selection_penalty_reasons"] = selection_penalty_reasons
        details.append(detail)
    return details


def baseline_run_from_verify_evidence(root: Path, task: dict[str, Any]) -> str | None:
    """Find a baseline run path from verify compare artifacts referenced by a task."""
    for entry in task.get("evidence", []):
        if not isinstance(entry, dict) or not entry.get("path"):
            continue
        evidence_path = resolve_evidence_path(root, str(entry["path"]))
        compare_path = (
            evidence_path
            if evidence_path.name == "compare.json"
            else evidence_path.parent / "compare.json"
        )
        compare = read_json_object(compare_path)
        if compare.get("kind") != "qa_z.verify_compare":
            continue
        baseline = compare.get("baseline")
        if isinstance(baseline, dict) and baseline.get("run_dir"):
            return str(baseline["run_dir"])
        baseline_run_id = compare.get("baseline_run_id")
        if baseline_run_id:
            return f".qa-z/runs/{baseline_run_id}"
    return None


def executor_dry_run_command(session_id: str | None) -> str:
    """Return the best local dry-run command for a selected task."""
    if session_id:
        return f"python -m qa_z executor-result dry-run --session {session_id}"
    return "python -m qa_z executor-result dry-run --session <session>"


def verification_observations(
    root: Path, selected_tasks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Return selected verification evidence observed by this loop."""
    observations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for task in selected_tasks:
        for entry in task.get("evidence", []):
            if not isinstance(entry, dict) or not entry.get("path"):
                continue
            path_text = str(entry["path"])
            path = resolve_evidence_path(root, path_text)
            if path.name != "summary.json" or path.parent.name != "verify":
                continue
            summary = read_json_object(path)
            verdict = summary.get("verdict")
            if not verdict or path_text in seen:
                continue
            observations.append(
                {
                    "path": path_text,
                    "verdict": str(verdict),
                    "regression_count": int_value(summary.get("regression_count")),
                    "new_issue_count": int_value(summary.get("new_issue_count")),
                }
            )
            seen.add(path_text)
    return observations


def existing_session_id(task: dict[str, Any]) -> str | None:
    """Extract an existing repair session id from task evidence paths."""
    for entry in task.get("evidence", []):
        if not isinstance(entry, dict) or not entry.get("path"):
            continue
        parts = Path(str(entry["path"]).replace("\\", "/")).parts
        for index, part in enumerate(parts):
            if part == "sessions" and index + 1 < len(parts):
                return parts[index + 1]
    return None


def update_history_entry(
    history_path: Path, *, loop_id: str, outcome: dict[str, Any]
) -> None:
    """Merge autonomy outcome fields into the existing selection history line."""
    if not history_path.is_file():
        return
    lines = history_path.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    updated = False
    for line in lines:
        entry = parse_json_line(line)
        if (
            not updated
            and entry.get("kind") == "qa_z.loop_history_entry"
            and entry.get("loop_id") == loop_id
        ):
            session_ids = outcome.get("created_session_ids") or []
            entry["resulting_session_id"] = session_ids[0] if session_ids else None
            entry["prepared_actions"] = [
                action.get("type") for action in outcome.get("actions_prepared", [])
            ]
            verification_evidence = outcome.get("verification_evidence", [])
            entry["verify_verdict"] = first_verify_verdict(verification_evidence)
            entry["outcome_path"] = outcome.get("artifacts", {}).get("outcome")
            entry["state"] = outcome.get("state")
            entry["state_transitions"] = outcome.get("state_transitions", [])
            entry["loop_elapsed_seconds"] = int_value(
                outcome.get("loop_elapsed_seconds")
            )
            entry["cumulative_elapsed_seconds"] = int_value(
                outcome.get("cumulative_elapsed_seconds")
            )
            entry["runtime_remaining_seconds"] = int_value(
                outcome.get("runtime_remaining_seconds")
            )
            entry["runtime_budget_met"] = bool(outcome.get("runtime_budget_met"))
            entry["backlog_open_count_before_inspection"] = int_value(
                outcome.get("backlog_open_count_before_inspection")
            )
            entry["backlog_open_count_after_inspection"] = int_value(
                outcome.get("backlog_open_count_after_inspection")
            )
            if outcome.get("selection_gap_reason"):
                entry["selection_gap_reason"] = str(outcome["selection_gap_reason"])
            if isinstance(outcome.get("loop_health"), dict):
                entry["loop_health"] = outcome["loop_health"]
            entry["next_recommendations"] = outcome.get("next_recommendations", [])
            updated_lines.append(json.dumps(entry, sort_keys=True))
            updated = True
        else:
            updated_lines.append(line)
    history_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")


def record_executor_result(
    history_path: Path,
    *,
    loop_id: str,
    result_status: str,
    ingest_status: str,
    verify_resume_status: str,
    result_path: str,
    validation_status: str,
    changed_files: list[str],
    verification_hint: str,
    verification_verdict: str | None,
    next_recommendation: str,
) -> None:
    """Merge executor-result fields into the matching loop history line."""
    if not history_path.is_file():
        return
    lines = history_path.read_text(encoding="utf-8").splitlines()
    updated_lines: list[str] = []
    updated = False
    for line in lines:
        entry = parse_json_line(line)
        if (
            not updated
            and entry.get("kind") == "qa_z.loop_history_entry"
            and entry.get("loop_id") == loop_id
        ):
            entry["executor_result_status"] = result_status
            entry["executor_ingest_status"] = ingest_status
            entry["executor_result_path"] = result_path
            entry["executor_validation_status"] = validation_status
            entry["executor_changed_files"] = list(changed_files)
            entry["executor_verification_hint"] = verification_hint
            entry["executor_verify_resume_status"] = verify_resume_status
            if verification_verdict:
                entry["verify_verdict"] = verification_verdict
            entry["next_recommendations"] = [next_recommendation]
            updated_lines.append(json.dumps(entry, sort_keys=True))
            updated = True
        else:
            updated_lines.append(line)
    history_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")


def first_verify_verdict(verification_evidence: object) -> str | None:
    """Return the first recorded verification verdict from outcome evidence."""
    if not isinstance(verification_evidence, list):
        return None
    for entry in verification_evidence:
        if isinstance(entry, dict) and entry.get("verdict"):
            return str(entry["verdict"])
    return None


def selection_gap_reason_for_loop(*, backlog_open_count_after_inspection: int) -> str:
    """Return a compact reason for a taskless loop."""
    if backlog_open_count_after_inspection <= 0:
        return "no_open_backlog_after_inspection"
    return "open_backlog_items_not_selected"


def current_open_sessions(root: Path) -> list[dict[str, str]]:
    """Return open repair sessions from local manifests."""
    sessions_root = root / ".qa-z" / "sessions"
    if not sessions_root.is_dir():
        return []
    sessions: list[dict[str, str]] = []
    for path in sorted(sessions_root.glob("*/session.json")):
        manifest = read_json_object(path)
        state = str(manifest.get("state") or "")
        if state not in OPEN_SESSION_STATES:
            continue
        session_id = str(manifest.get("session_id") or path.parent.name)
        sessions.append(
            {
                "session_id": session_id,
                "state": state,
                "session_dir": format_path(path.parent, root),
            }
        )
    return sessions


def backlog_top_items(root: Path) -> list[dict[str, Any]]:
    """Return a compact top-five backlog view."""
    items = [
        item
        for item in load_backlog(root).get("items", [])
        if isinstance(item, dict) and str(item.get("status", "open")) == "open"
    ]
    items = sorted(
        items,
        key=lambda item: (
            -int_value(item.get("priority_score")),
            str(item.get("category", "")),
            str(item.get("id", "")),
        ),
    )
    return [
        {
            "id": str(item.get("id")),
            "category": str(item.get("category")),
            "priority_score": int_value(item.get("priority_score")),
            "status": str(item.get("status", "open")),
            "title": str(item.get("title") or ""),
            "recommendation": str(item.get("recommendation") or ""),
            "evidence_summary": compact_backlog_evidence_summary(item),
        }
        for item in items[:5]
    ]


def latest_verify_observation(root: Path) -> str | None:
    """Return the newest verification verdict if local verify summaries exist."""
    qa_root = root / ".qa-z"
    if not qa_root.is_dir():
        return None
    summaries = [
        path for path in qa_root.rglob("verify/summary.json") if path.is_file()
    ]
    if not summaries:
        return None
    latest = max(summaries, key=lambda path: (path.stat().st_mtime, str(path)))
    summary = read_json_object(latest)
    verdict = summary.get("verdict")
    return str(verdict) if verdict else None


def autonomy_loop_id(generated_at: str, index: int) -> str:
    """Create a stable loop id from a timestamp and loop ordinal."""
    digits = re.sub(r"\D", "", generated_at)
    if len(digits) < 14:
        digits = re.sub(r"\D", "", utc_now()).ljust(14, "0")
    return f"loop-{digits[:8]}-{digits[8:14]}-{index:02d}"


def loops_root(root: Path) -> Path:
    """Return the autonomy loops directory."""
    return root / ".qa-z" / "loops"


def with_runtime_fields(
    *,
    outcome: dict[str, Any],
    loop_started_at: str,
    loop_finished_at: str,
    loop_elapsed_seconds: int,
    cumulative_elapsed_seconds: int,
    runtime_target_seconds: int,
    min_loop_seconds: int,
    runtime_budget_met: bool,
) -> dict[str, Any]:
    """Attach runtime-budget accounting fields to one autonomy outcome."""
    enriched = dict(outcome)
    enriched["loop_started_at"] = loop_started_at
    enriched["loop_finished_at"] = loop_finished_at
    enriched["loop_elapsed_seconds"] = loop_elapsed_seconds
    enriched["cumulative_elapsed_seconds"] = cumulative_elapsed_seconds
    enriched["runtime_target_seconds"] = runtime_target_seconds
    enriched["runtime_remaining_seconds"] = max(
        runtime_target_seconds - cumulative_elapsed_seconds, 0
    )
    enriched["min_loop_seconds"] = min_loop_seconds
    enriched["runtime_budget_met"] = runtime_budget_met
    return enriched


def write_outcome_artifact(root: Path, outcome: dict[str, Any]) -> None:
    """Rewrite the loop and latest outcome artifacts after runtime enrichment."""
    outcome_path = outcome.get("artifacts", {}).get("outcome")
    if not outcome_path:
        return
    path = resolve_evidence_path(root, str(outcome_path))
    write_json(path, outcome)
    latest_dir = loops_root(root) / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    copy_artifact(path, latest_dir / "outcome.json")


def resolve_evidence_path(root: Path, value: str) -> Path:
    """Resolve an evidence path relative to the repository root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def copy_artifact(source: Path, target: Path) -> None:
    """Copy an artifact to a loop directory, preserving exact bytes."""
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def read_json_object(path: Path) -> dict[str, Any]:
    """Read an optional JSON object."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a stable JSON object artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def parse_json_line(line: str) -> dict[str, Any]:
    """Parse one JSONL line, returning an empty mapping on failure."""
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def coerce_duration_seconds(value: object) -> int:
    """Return a non-negative integer number of seconds."""
    try:
        seconds = float(str(value))
    except (TypeError, ValueError):
        return 0
    if seconds <= 0:
        return 0
    return int(math.ceil(seconds))
