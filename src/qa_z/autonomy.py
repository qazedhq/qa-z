"""Deterministic autonomy workflow loops for QA-Z planning."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from qa_z.artifacts import format_path
from qa_z.autonomy_actions import action_for_task
from qa_z.autonomy_records import (
    autonomy_loop_id,
    copy_artifact,
    coerce_duration_seconds,
    loops_root,
    read_json_object,
    record_executor_result,
    update_history_entry,
    utc_now,
    with_runtime_fields,
    write_json,
    write_outcome_artifact,
)
from qa_z.autonomy_plan import build_loop_health, render_autonomy_loop_plan
from qa_z.autonomy_selection import (
    autonomy_selection_context,
    blocked_no_candidate_chain_length,
    blocked_no_candidate_chain_loop_ids,
    is_fallback_selection_task,
    next_recommendations,
    selection_gap_reason_for_loop,
    verification_observations,
    with_loop_local_self_inspection_context,
)
from qa_z.autonomy_status import (
    load_autonomy_status,
    render_autonomy_status,
    render_autonomy_summary,
)
from qa_z.improvement_state import load_backlog, open_backlog_items
from qa_z.repair_session import create_repair_session
from qa_z.self_improvement import (
    SELF_IMPROVEMENT_SCHEMA_VERSION,
    run_self_inspection,
    select_next_tasks,
)
from qa_z.task_selection import (
    evidence_paths,
    fallback_families_for_items,
)

AUTONOMY_SUMMARY_KIND = "qa_z.autonomy_summary"
AUTONOMY_OUTCOME_KIND = "qa_z.autonomy_outcome"


@dataclass(frozen=True)
class AutonomyDependencies:
    """Injectable autonomy helpers for tests and future seam refactors."""

    load_backlog: Callable[[Path], dict[str, Any]] = load_backlog
    open_backlog_items: Callable[[dict[str, Any]], list[dict[str, Any]]] = (
        open_backlog_items
    )
    run_self_inspection: Callable[..., Any] = run_self_inspection
    select_next_tasks: Callable[..., Any] = select_next_tasks
    create_repair_session: Callable[..., Any] = create_repair_session


DEFAULT_AUTONOMY_DEPENDENCIES = AutonomyDependencies()

__all__ = [
    "AutonomyDependencies",
    "action_for_task",
    "load_autonomy_status",
    "record_executor_result",
    "render_autonomy_loop_plan",
    "render_autonomy_status",
    "render_autonomy_summary",
    "run_autonomy",
    "run_autonomy_loop",
]

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
    deps: AutonomyDependencies | None = None,
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
    resolved_deps = deps or DEFAULT_AUTONOMY_DEPENDENCIES
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
            deps=resolved_deps,
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
    deps: AutonomyDependencies | None = None,
) -> dict[str, Any]:
    """Run one inspect/select/plan/record autonomy loop."""
    resolved_deps = deps or DEFAULT_AUTONOMY_DEPENDENCIES
    transitions = ["inspected"]
    backlog_before = resolved_deps.load_backlog(root)
    backlog_open_count_before_inspection = len(
        resolved_deps.open_backlog_items(backlog_before)
    )
    empty_backlog_detected = backlog_open_count_before_inspection == 0
    inspection_paths = resolved_deps.run_self_inspection(
        root=root, now=generated_at, loop_id=loop_id
    )
    backlog_after = resolved_deps.load_backlog(root)
    backlog_open_count_after_inspection = len(
        resolved_deps.open_backlog_items(backlog_after)
    )
    selection_paths = resolved_deps.select_next_tasks(
        root=root, count=count, now=generated_at, loop_id=loop_id
    )
    transitions.append("selected")

    selected_artifact = read_json_object(selection_paths.selected_tasks_path)
    selected_tasks = [
        item
        for item in selected_artifact.get("selected_tasks", [])
        if isinstance(item, dict)
    ]
    selected_artifact = with_loop_local_self_inspection_context(
        selected_artifact, loop_id=loop_id, generated_at=generated_at
    )
    write_json(selection_paths.selected_tasks_path, selected_artifact)
    selection_context = autonomy_selection_context(selected_artifact)
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
    loop_dir = loops_root(root) / loop_id
    latest_dir = loops_root(root) / "latest"
    loop_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    copy_artifact(inspection_paths.self_inspection_path, loop_dir / "self_inspect.json")
    observed_verification = verification_observations(root, selected_tasks)
    if observed_verification:
        transitions.append("verification_observed")
    actions = [
        action_for_task(
            root=root,
            config=config,
            loop_id=loop_id,
            task=task,
            deps=resolved_deps,
        )
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

    copy_artifact(selection_paths.selected_tasks_path, loop_dir / "selected_tasks.json")
    selected_task_ids = [str(task.get("id")) for task in selected_tasks]
    selected_fallback_families = fallback_families_for_items(selected_tasks)
    transitions.extend(["recorded", "completed"])
    state = "completed"
    if fallback_selected:
        state = "fallback_selected"
    elif not selected_tasks:
        state = "blocked_no_candidates"
    blocked_chain_length = blocked_no_candidate_chain_length(
        selection_paths.history_path,
        current_state=state,
        current_loop_id=loop_id,
    )
    blocked_chain_loop_ids = blocked_no_candidate_chain_loop_ids(
        selection_paths.history_path,
        current_state=state,
        current_loop_id=loop_id,
    )
    loop_health = build_loop_health(
        selected_count=len(selected_tasks),
        fallback_selected=fallback_selected,
        selection_gap_reason=selection_gap_reason,
        backlog_open_count_before_inspection=backlog_open_count_before_inspection,
        backlog_open_count_after_inspection=backlog_open_count_after_inspection,
        blocked_chain_length=blocked_chain_length,
        blocked_chain_loop_ids=blocked_chain_loop_ids,
        blocked_stop_threshold=MAX_CONSECUTIVE_BLOCKED_LOOPS,
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
        live_repository=selection_context.get("live_repository"),
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
    outcome.update(selection_context)
    if selection_gap_reason:
        outcome["selection_gap_reason"] = selection_gap_reason
    write_json(loop_dir / "outcome.json", outcome)
    copy_artifact(loop_dir / "self_inspect.json", latest_dir / "self_inspect.json")
    copy_artifact(loop_dir / "selected_tasks.json", latest_dir / "selected_tasks.json")
    copy_artifact(loop_dir / "outcome.json", latest_dir / "outcome.json")
    update_history_entry(selection_paths.history_path, loop_id=loop_id, outcome=outcome)
    return outcome
