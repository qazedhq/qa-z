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

from qa_z.self_improvement import (
    compact_backlog_evidence_summary,
    evidence_paths,
    int_value,
    load_backlog,
    open_backlog_items,
    run_self_inspection,
    select_next_tasks,
    selected_task_action_hint,
    selected_task_validation_command,
)

AUTONOMY_SCHEMA_VERSION = 1
AUTONOMY_SUMMARY_KIND = "qa_z.autonomy_summary"
AUTONOMY_OUTCOME_KIND = "qa_z.autonomy_outcome"
AUTONOMY_STATUS_KIND = "qa_z.autonomy_status"
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
    del config
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    generated_at = now or utc_now()
    loops_requested = max(1, int_value(loops, default=1))
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
            loop_id=autonomy_loop_id(generated_at, loop_index),
            generated_at=loop_generated_at,
            count=count,
        )
        loop_elapsed = max(0.0, monotonic_fn() - loop_started_monotonic)
        remaining_loop_time = max(0.0, minimum_loop_seconds - loop_elapsed)
        if remaining_loop_time > 0:
            sleep_fn(remaining_loop_time)
        loop_elapsed_seconds = coerce_duration_seconds(
            max(0.0, monotonic_fn() - loop_started_monotonic)
        )
        cumulative_elapsed_seconds = coerce_duration_seconds(
            max(0.0, monotonic_fn() - run_started_monotonic)
        )
        runtime_budget_met = cumulative_elapsed_seconds >= runtime_target_seconds
        enriched_outcome = with_runtime_fields(
            outcome=outcome,
            loop_started_at=loop_generated_at,
            loop_finished_at=now or utc_now(),
            loop_elapsed_seconds=loop_elapsed_seconds,
            cumulative_elapsed_seconds=cumulative_elapsed_seconds,
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
    summary = {
        "kind": AUTONOMY_SUMMARY_KIND,
        "schema_version": AUTONOMY_SCHEMA_VERSION,
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
        "outcomes": outcomes,
    }
    latest_dir = loops_root(root) / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    write_json(latest_dir / "autonomy_summary.json", summary)
    return summary


def run_autonomy_loop(
    *, root: Path, loop_id: str, generated_at: str, count: int
) -> dict[str, Any]:
    """Run one inspect/select/plan/record autonomy loop."""
    transitions = ["inspected"]
    inspection_paths = run_self_inspection(
        root=root,
        loop_id=loop_id,
        generated_at=generated_at,
    )
    selection_paths = select_next_tasks(
        root=root,
        count=count,
        loop_id=loop_id,
        generated_at=generated_at,
    )
    transitions.append("selected")
    selected_artifact = read_json_object(selection_paths.selected_tasks_path)
    selected_tasks = [
        item
        for item in selected_artifact.get("selected_tasks", [])
        if isinstance(item, dict)
    ]
    actions = [
        action_for_task(root=root, loop_id=loop_id, task=task)
        for task in selected_tasks
    ]
    selected_task_ids = [str(task.get("id")) for task in selected_tasks]
    state = "completed"
    if selected_tasks:
        transitions.append("awaiting_repair")
    else:
        state = "blocked_no_candidates"
        transitions.append("blocked_no_candidates")
    transitions.extend(["recorded", "completed"])

    loop_dir = loops_root(root) / loop_id
    latest_dir = loops_root(root) / "latest"
    loop_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    copy_artifact(inspection_paths.self_inspection_path, loop_dir / "self_inspect.json")
    copy_artifact(selection_paths.selected_tasks_path, loop_dir / "selected_tasks.json")
    plan_text = render_autonomy_loop_plan(
        loop_id=loop_id,
        generated_at=generated_at,
        selected_tasks=selected_tasks,
        actions=actions,
    )
    (loop_dir / "loop_plan.md").write_text(plan_text, encoding="utf-8")
    (latest_dir / "loop_plan.md").write_text(plan_text, encoding="utf-8")
    outcome = {
        "kind": AUTONOMY_OUTCOME_KIND,
        "schema_version": AUTONOMY_SCHEMA_VERSION,
        "loop_id": loop_id,
        "generated_at": generated_at,
        "state": state,
        "state_transitions": transitions,
        "selected_task_ids": selected_task_ids,
        "evidence_used": evidence_paths(selected_tasks),
        "actions_prepared": actions,
        "next_recommendations": next_recommendations(selected_tasks, actions),
        "artifacts": {
            "self_inspection": relative_path(loop_dir / "self_inspect.json", root),
            "selected_tasks": relative_path(loop_dir / "selected_tasks.json", root),
            "loop_plan": relative_path(loop_dir / "loop_plan.md", root),
            "outcome": relative_path(loop_dir / "outcome.json", root),
        },
    }
    write_json(loop_dir / "outcome.json", outcome)
    copy_artifact(loop_dir / "self_inspect.json", latest_dir / "self_inspect.json")
    copy_artifact(loop_dir / "selected_tasks.json", latest_dir / "selected_tasks.json")
    copy_artifact(loop_dir / "outcome.json", latest_dir / "outcome.json")
    update_history_entry(selection_paths.history_path, loop_id=loop_id, outcome=outcome)
    return outcome


def action_for_task(
    *, root: Path, loop_id: str, task: dict[str, Any]
) -> dict[str, Any]:
    """Translate one selected backlog task into a deterministic next action."""
    del root, loop_id
    task_id = str(task.get("id") or "unknown")
    category = str(task.get("category") or "")
    recommendation = str(task.get("recommendation") or "")
    validation_command = selected_task_validation_command(task)
    if recommendation == "add_benchmark_fixture" or category == "benchmark_failure":
        return prepared_action(
            task_id=task_id,
            action_type="benchmark_fixture_plan",
            title="Repair benchmark expectation or add deterministic fixture coverage.",
            next_recommendation="run qa-z benchmark after fixture updates",
            commands=[validation_command],
        )
    if (
        recommendation == "repair_verification_regression"
        or category == "verification_regression"
    ):
        return prepared_action(
            task_id=task_id,
            action_type="verification_stabilization_plan",
            title="Use verification evidence to stabilize the regressed deterministic check.",
            next_recommendation="rerun the targeted self-improvement and CLI tests after repair",
            commands=[validation_command],
        )
    if recommendation == "sync_contract_and_docs" or category in {
        "artifact_schema_gap",
        "docs_drift",
    }:
        return prepared_action(
            task_id=task_id,
            action_type="docs_sync_plan",
            title="Synchronize public docs and artifact schema with implemented behavior.",
            next_recommendation="rerun artifact-schema and CLI tests after docs sync",
            commands=[validation_command],
        )
    return prepared_action(
        task_id=task_id,
        action_type="implementation_plan",
        title=selected_task_action_hint(task),
        next_recommendation="turn selected evidence into a scoped deterministic repair",
        commands=[validation_command],
    )


def prepared_action(
    *,
    task_id: str,
    action_type: str,
    title: str,
    next_recommendation: str,
    commands: list[str],
) -> dict[str, Any]:
    """Return a normalized prepared action."""
    return {
        "type": action_type,
        "task_id": task_id,
        "title": title,
        "next_recommendation": next_recommendation,
        "commands": commands,
    }


def render_autonomy_loop_plan(
    *,
    loop_id: str,
    generated_at: str,
    selected_tasks: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> str:
    """Render a human-readable loop plan for the current autonomy loop."""
    lines = [
        "# QA-Z Autonomy Loop Plan",
        "",
        f"Loop: `{loop_id}`",
        f"Generated at: `{generated_at}`",
        "",
        "This plan is artifact-only. It prepares local work and does not edit code autonomously.",
        "",
    ]
    if not selected_tasks:
        lines.extend(
            [
                "## Selected Tasks",
                "",
                "No open backlog tasks were selected.",
                "",
                "## Prepared Actions",
                "",
                "- none",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(["## Selected Tasks", ""])
    for task in selected_tasks:
        lines.extend(
            [
                f"- `{task.get('id')}`: {task.get('title')}",
                f"  - category: `{task.get('category')}`",
                f"  - recommendation: `{task.get('recommendation')}`",
                f"  - score: {task.get('priority_score')}",
                f"  - evidence: {compact_backlog_evidence_summary(task)}",
            ]
        )
    lines.extend(["", "## Prepared Actions", ""])
    if not actions:
        lines.append("- none")
    for action in actions:
        commands = "; ".join(str(item) for item in action.get("commands", []))
        lines.extend(
            [
                f"- `{action.get('type')}` for `{action.get('task_id')}`",
                f"  - next: {action.get('next_recommendation')}",
                f"  - commands: {commands}",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def load_autonomy_status(root: Path) -> dict[str, Any]:
    """Load a compact status view for the most recent autonomy loop."""
    root = root.resolve()
    latest_dir = loops_root(root) / "latest"
    summary = read_json_object(latest_dir / "autonomy_summary.json")
    outcome = read_json_object(latest_dir / "outcome.json")
    selected = read_json_object(latest_dir / "selected_tasks.json")
    selected_tasks = [
        item for item in selected.get("selected_tasks", []) if isinstance(item, dict)
    ]
    status = {
        "kind": AUTONOMY_STATUS_KIND,
        "schema_version": AUTONOMY_SCHEMA_VERSION,
        "latest_loop_id": outcome.get("loop_id") or summary.get("latest_loop_id"),
        "latest_state": outcome.get("state"),
        "latest_selected_tasks": [str(item.get("id")) for item in selected_tasks],
        "latest_selected_task_details": status_selected_task_details(selected_tasks),
        "latest_prepared_actions": status_prepared_actions(
            outcome.get("actions_prepared", [])
        ),
        "latest_next_recommendations": list(outcome.get("next_recommendations", [])),
        "runtime_target_seconds": int_value(summary.get("runtime_target_seconds")),
        "runtime_elapsed_seconds": int_value(summary.get("runtime_elapsed_seconds")),
        "runtime_remaining_seconds": int_value(
            summary.get("runtime_remaining_seconds")
        ),
        "runtime_budget_met": bool(summary.get("runtime_budget_met", True)),
        "min_loop_seconds": int_value(summary.get("min_loop_seconds")),
        "backlog_top_items": backlog_top_items(root),
    }
    return status


def render_autonomy_summary(summary: dict[str, Any], root: Path) -> str:
    """Render human output for qa-z autonomy."""
    del root
    lines = [
        f"qa-z autonomy: {summary.get('loops_completed', 0)} loop(s)",
        f"Latest loop: {summary.get('latest_loop_id') or 'none'}",
        "Runtime: "
        + format_runtime_progress(
            elapsed_seconds=int_value(summary.get("runtime_elapsed_seconds")),
            target_seconds=int_value(summary.get("runtime_target_seconds")),
        ),
        f"Minimum loop seconds: {summary.get('min_loop_seconds', 0)}",
        f"Stop reason: {summary.get('stop_reason')}",
    ]
    return "\n".join(lines)


def render_autonomy_status(status: dict[str, Any]) -> str:
    """Render human output for qa-z autonomy status."""
    lines = [
        f"Latest loop: {status.get('latest_loop_id') or 'none'}",
        f"State: {status.get('latest_state') or 'none'}",
        "Runtime: "
        + format_runtime_progress(
            elapsed_seconds=int_value(status.get("runtime_elapsed_seconds")),
            target_seconds=int_value(status.get("runtime_target_seconds")),
        ),
        f"Minimum loop seconds: {status.get('min_loop_seconds', 0)}",
        "Selected tasks:",
    ]
    selected_tasks = status.get("latest_selected_tasks") or []
    if not selected_tasks:
        lines.append("- none")
    for task_id in selected_tasks:
        lines.append(f"- {task_id}")
    lines.append("Prepared actions:")
    prepared_actions = status.get("latest_prepared_actions") or []
    if not prepared_actions:
        lines.append("- none")
    for action in prepared_actions:
        lines.append(f"- {action.get('type')} for {action.get('task_id')}")
        if action.get("next_recommendation"):
            lines.append(f"  next: {action['next_recommendation']}")
        commands = action.get("commands") or []
        if commands:
            lines.append(f"  commands: {'; '.join(str(item) for item in commands)}")
    lines.append("Backlog top items:")
    backlog_items = status.get("backlog_top_items") or []
    if not backlog_items:
        lines.append("- none")
    for item in backlog_items:
        lines.append(
            f"- {item.get('id')}: priority {item.get('priority_score')} "
            f"({item.get('category')})"
        )
    return "\n".join(lines)


def next_recommendations(
    selected_tasks: list[dict[str, Any]], actions: list[dict[str, Any]]
) -> list[str]:
    """Return compact next recommendations from prepared actions."""
    if not selected_tasks:
        return ["no open backlog tasks selected"]
    return [
        str(action["next_recommendation"])
        for action in actions
        if action.get("next_recommendation")
    ] or ["prepare selected task evidence for local repair"]


def status_prepared_actions(actions: object) -> list[dict[str, Any]]:
    """Return compact prepared actions for status output."""
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
        prepared.append(compact)
    return prepared


def status_selected_task_details(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return compact selected-task details for status output."""
    details: list[dict[str, Any]] = []
    for item in items:
        details.append(
            {
                "id": str(item.get("id") or "unknown"),
                "title": str(item.get("title") or item.get("id") or "untitled"),
                "category": str(item.get("category") or ""),
                "recommendation": str(item.get("recommendation") or ""),
                "priority_score": int_value(item.get("priority_score")),
                "evidence_summary": compact_backlog_evidence_summary(item),
            }
        )
    return details


def backlog_top_items(root: Path) -> list[dict[str, Any]]:
    """Return a compact top-five backlog view."""
    items = sorted(
        open_backlog_items(load_backlog(root)),
        key=lambda item: (
            -int_value(item.get("priority_score")),
            str(item.get("category") or ""),
            str(item.get("id") or ""),
        ),
    )
    return [
        {
            "id": str(item.get("id")),
            "category": str(item.get("category")),
            "priority_score": int_value(item.get("priority_score")),
            "status": str(item.get("status") or "open"),
            "title": str(item.get("title") or ""),
            "recommendation": str(item.get("recommendation") or ""),
            "evidence_summary": compact_backlog_evidence_summary(item),
        }
        for item in items[:5]
    ]


def update_history_entry(
    history_path: Path, *, loop_id: str, outcome: dict[str, Any]
) -> None:
    """Merge autonomy outcome fields into the matching selection history line."""
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
            entry["outcome_path"] = outcome.get("artifacts", {}).get("outcome")
            entry["state"] = outcome.get("state")
            entry["state_transitions"] = outcome.get("state_transitions", [])
            entry["prepared_actions"] = [
                action.get("type") for action in outcome.get("actions_prepared", [])
            ]
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
            entry["next_recommendations"] = outcome.get("next_recommendations", [])
            updated_lines.append(json.dumps(entry, sort_keys=True))
            updated = True
        else:
            updated_lines.append(line)
    history_path.write_text("\n".join(updated_lines).rstrip() + "\n", encoding="utf-8")


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
    """Rewrite loop and latest outcome artifacts after runtime enrichment."""
    outcome_path = outcome.get("artifacts", {}).get("outcome")
    if not outcome_path:
        return
    path = resolve_root_path(root, str(outcome_path))
    write_json(path, outcome)
    latest_dir = loops_root(root) / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    copy_artifact(path, latest_dir / "outcome.json")


def format_runtime_progress(*, elapsed_seconds: int, target_seconds: int) -> str:
    """Render runtime progress without an elapsed/0 display."""
    if target_seconds <= 0:
        return f"{elapsed_seconds} seconds elapsed (no minimum budget)"
    return f"{elapsed_seconds}/{target_seconds} seconds"


def autonomy_loop_id(generated_at: str, index: int) -> str:
    """Create a stable loop id from a timestamp and loop ordinal."""
    digits = re.sub(r"\D", "", generated_at)
    if len(digits) < 14:
        digits = re.sub(r"\D", "", utc_now()).ljust(14, "0")
    return f"loop-{digits[:8]}-{digits[8:14]}-{index:02d}"


def loops_root(root: Path) -> Path:
    """Return the autonomy loops directory."""
    return root / ".qa-z" / "loops"


def resolve_root_path(root: Path, value: str) -> Path:
    """Resolve a repository-relative path."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def relative_path(path: Path, root: Path) -> str:
    """Render a repository-relative path when possible."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


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
