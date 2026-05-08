"""Status-loading and rendering helpers for autonomy workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.autonomy_records import loops_root, read_json_object
from qa_z.improvement_state import load_backlog
from qa_z.live_repository import render_live_repository_summary
from qa_z.operator_commands import AUTONOMY_ONE_LOOP_COMMAND
from qa_z.operator_commands import AUTONOMY_STATUS_JSON_COMMAND
from qa_z.repair_signals import iter_live_verification_summary_paths
from qa_z.self_improvement import SELF_IMPROVEMENT_SCHEMA_VERSION, int_value
from qa_z.task_selection import compact_backlog_evidence_summary
from qa_z.task_selection import selected_task_action_hint
from qa_z.task_selection import selected_task_validation_command
from qa_z.task_selection import worktree_patch_add_command_texts

AUTONOMY_STATUS_KIND = "qa_z.autonomy_status"

OPEN_SESSION_STATES = {
    "created",
    "handoff_ready",
    "waiting_for_external_repair",
    "candidate_generated",
    "verification_complete",
    "failed",
}

__all__ = [
    "load_autonomy_status",
    "render_autonomy_status",
    "render_autonomy_summary",
    "status_prepared_actions",
]


def load_autonomy_status(root: Path) -> dict[str, Any]:
    """Load a compact status view of the latest autonomy artifacts."""
    root = root.resolve()
    latest_dir = loops_root(root) / "latest"
    summary = read_json_object(latest_dir / "autonomy_summary.json")
    outcome = read_json_object(latest_dir / "outcome.json")
    selected = read_json_object(latest_dir / "selected_tasks.json")
    selected_loop_id = str(selected.get("loop_id") or "").strip()
    outcome_loop_id = str(outcome.get("loop_id") or "").strip()
    selected_tasks = [
        item
        for item in selected.get("selected_tasks", [])
        if isinstance(item, dict) and item.get("id")
    ]
    open_sessions = current_open_sessions(root)
    backlog = load_backlog(root)
    backlog_items = backlog_top_items_from_backlog(backlog)
    recent_verify = latest_verify_observation(root)
    prepared_actions = status_prepared_actions(outcome.get("actions_prepared"))
    prepared_actions_stale = bool(
        prepared_actions
        and selected_loop_id
        and outcome_loop_id
        and selected_loop_id != outcome_loop_id
    )
    next_actions = [
        str(item)
        for item in outcome.get("next_recommendations", [])
        if isinstance(item, str) and item.strip()
    ]
    next_recommendations_stale = bool(
        next_actions
        and selected_loop_id
        and outcome_loop_id
        and selected_loop_id != outcome_loop_id
    )
    return {
        "kind": AUTONOMY_STATUS_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "latest_loop_id": outcome.get("loop_id"),
        "latest_outcome_loop_id": outcome_loop_id or None,
        "latest_selected_loop_id": selected_loop_id or None,
        "latest_selection_outcome_mismatch": bool(
            selected_loop_id and outcome_loop_id and selected_loop_id != outcome_loop_id
        ),
        "latest_state": outcome.get("state"),
        "latest_source_self_inspection": selected.get("source_self_inspection")
        or outcome.get("source_self_inspection"),
        "latest_source_self_inspection_loop_id": selected.get(
            "source_self_inspection_loop_id"
        )
        or outcome.get("source_self_inspection_loop_id"),
        "latest_source_self_inspection_generated_at": selected.get(
            "source_self_inspection_generated_at"
        )
        or outcome.get("source_self_inspection_generated_at"),
        "latest_selected_tasks": [str(item["id"]) for item in selected_tasks],
        "latest_selected_fallback_families": [
            str(item)
            for item in outcome.get("selected_fallback_families", [])
            if isinstance(item, str) and item.strip()
        ],
        "latest_live_repository": selected.get("live_repository")
        if isinstance(selected.get("live_repository"), dict)
        and selected.get("live_repository")
        else outcome.get("live_repository", {}),
        "latest_selected_task_details": status_selected_task_details(selected_tasks),
        "latest_prepared_actions": prepared_actions,
        "latest_prepared_actions_loop_id": outcome_loop_id
        if prepared_actions and outcome_loop_id
        else None,
        "latest_prepared_actions_stale_for_selection": prepared_actions_stale,
        "latest_prepared_actions_refresh_commands": (
            stale_autonomy_status_refresh_commands() if prepared_actions_stale else []
        ),
        "latest_next_recommendations": next_actions,
        "latest_next_recommendations_stale_for_selection": (next_recommendations_stale),
        "latest_next_recommendations_refresh_commands": (
            stale_autonomy_status_refresh_commands()
            if next_recommendations_stale
            else []
        ),
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
        "backlog_updated_at": backlog.get("updated_at")
        or backlog.get("generated_at")
        or None,
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
    ]
    backlog_updated_at = str(status.get("backlog_updated_at") or "").strip()
    if backlog_updated_at:
        lines.append(f"Backlog updated: {backlog_updated_at}")
    lines.append("Selected task details:")
    selected_loop_id = str(status.get("latest_selected_loop_id") or "").strip()
    outcome_loop_id = str(status.get("latest_outcome_loop_id") or "").strip()
    if selected_loop_id:
        lines.append(f"Selected task loop: {selected_loop_id}")
    if outcome_loop_id:
        lines.append(f"Outcome loop: {outcome_loop_id}")
    if status.get("latest_selection_outcome_mismatch"):
        lines.append("Selection/outcome loop mismatch: true")
    source_self_inspection = str(
        status.get("latest_source_self_inspection") or ""
    ).strip()
    if source_self_inspection:
        lines.append(f"Self-inspection source: {source_self_inspection}")
    source_loop_id = str(
        status.get("latest_source_self_inspection_loop_id") or ""
    ).strip()
    source_generated_at = str(
        status.get("latest_source_self_inspection_generated_at") or ""
    ).strip()
    if source_loop_id or source_generated_at:
        if source_loop_id and source_generated_at:
            lines.append(
                f"Self-inspection loop: {source_loop_id} ({source_generated_at})"
            )
        else:
            lines.append(
                "Self-inspection loop: "
                + (source_loop_id or "unknown")
                + (f" ({source_generated_at})" if source_generated_at else "")
            )
    if selected_fallback_families:
        lines.append(
            "Selected fallback families: " + ", ".join(selected_fallback_families)
        )
    if isinstance(status.get("latest_live_repository"), dict) and status.get(
        "latest_live_repository"
    ):
        lines.append(
            "Live repository: "
            + render_live_repository_summary(status.get("latest_live_repository"))
        )
    if loop_health:
        lines.append(f"Loop health: {loop_health.get('classification') or 'unknown'}")
        if loop_health.get("summary"):
            lines.append(f"Loop health summary: {loop_health['summary']}")
        if loop_health.get("blocked_chain_length"):
            lines.append(
                "Blocked no-candidate chain: "
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
                "Blocked no-candidate loop ids: " + ", ".join(blocked_chain_loop_ids)
            )
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
        if item.get("action_hint"):
            lines.append(f"  action: {item['action_hint']}")
        patch_commands = [
            str(command)
            for command in item.get("patch_commands", [])
            if isinstance(command, str) and command.strip()
        ]
        if patch_commands:
            lines.append("  patch-add commands:")
            lines.extend(f"    - {command}" for command in patch_commands)
        if item.get("validation_command"):
            lines.append(f"  validation: {item['validation_command']}")
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
    lines.extend(["Prepared actions:"])
    if prepared_actions:
        prepared_actions_loop_id = str(
            status.get("latest_prepared_actions_loop_id") or ""
        ).strip()
        if prepared_actions_loop_id:
            lines.append(f"Prepared actions loop: {prepared_actions_loop_id}")
        if status.get("latest_prepared_actions_stale_for_selection"):
            lines.append(
                "Prepared actions may not match the latest selected task artifact."
            )
            refresh_commands = [
                str(command)
                for command in status.get(
                    "latest_prepared_actions_refresh_commands", []
                )
                if isinstance(command, str) and command.strip()
            ]
            if refresh_commands:
                lines.append("Prepared action refresh commands:")
                lines.extend(f"  - {command}" for command in refresh_commands)
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
            lines.append("  commands:")
            lines.extend(f"    - {item}" for item in commands)
        context_paths = action.get("context_paths")
        if isinstance(context_paths, list) and context_paths:
            lines.append("  context:")
            lines.extend(f"    - {item}" for item in context_paths)
    lines.extend(["Next recommendations:"])
    if not next_steps:
        lines.append("- none")
    elif status.get("latest_next_recommendations_stale_for_selection"):
        lines.append(
            "Next recommendations may not match the latest selected task artifact."
        )
        refresh_commands = [
            str(command)
            for command in status.get(
                "latest_next_recommendations_refresh_commands", []
            )
            if isinstance(command, str) and command.strip()
        ]
        if refresh_commands:
            lines.append("Next recommendation refresh commands:")
            lines.extend(f"  - {command}" for command in refresh_commands)
    for recommendation in next_steps:
        lines.append(f"- {recommendation}")
    lines.extend(["Backlog top items:"])
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
        if item.get("action_hint"):
            lines.append(f"  action: {item['action_hint']}")
        patch_commands = [
            str(command)
            for command in item.get("patch_commands", [])
            if isinstance(command, str) and command.strip()
        ]
        if patch_commands:
            lines.append("  patch-add commands:")
            lines.extend(f"    - {command}" for command in patch_commands)
        if item.get("validation_command"):
            lines.append(f"  validation: {item['validation_command']}")
        if item.get("evidence_summary"):
            lines.append(f"  evidence: {item['evidence_summary']}")
    return "\n".join(lines)


def stale_autonomy_status_refresh_commands() -> list[str]:
    """Return local commands that regenerate stale autonomy status handoff data."""
    return [AUTONOMY_ONE_LOOP_COMMAND, AUTONOMY_STATUS_JSON_COMMAND]


def format_runtime_progress(*, elapsed_seconds: int, target_seconds: int) -> str:
    """Render runtime progress without the confusing elapsed/0 form."""
    if target_seconds <= 0:
        return f"{elapsed_seconds} seconds elapsed (no minimum budget)"
    return f"{elapsed_seconds}/{target_seconds} seconds"


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
            "action_hint": str(
                item.get("action_hint") or selected_task_action_hint(item)
            ),
            "validation_command": str(
                item.get("validation_command") or selected_task_validation_command(item)
            ),
            "evidence_summary": str(
                item.get("evidence_summary") or compact_backlog_evidence_summary(item)
            ),
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
        patch_commands = worktree_patch_add_command_texts(item)
        if patch_commands:
            detail["patch_commands"] = patch_commands
        details.append(detail)
    return details


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
    return backlog_top_items_from_backlog(load_backlog(root))


def backlog_top_items_from_backlog(backlog: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a compact top-five backlog view from one backlog snapshot."""
    items = [
        item
        for item in backlog.get("items", [])
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
            "action_hint": selected_task_action_hint(item),
            "validation_command": selected_task_validation_command(item),
            "evidence_summary": compact_backlog_evidence_summary(item),
            **(
                {"patch_commands": patch_commands}
                if (patch_commands := worktree_patch_add_command_texts(item))
                else {}
            ),
        }
        for item in items[:5]
    ]


def latest_verify_observation(root: Path) -> str | None:
    """Return the newest verification verdict if local verify summaries exist."""
    summaries = iter_live_verification_summary_paths(root)
    if not summaries:
        return None
    latest = max(summaries, key=lambda path: (path.stat().st_mtime, str(path)))
    summary = read_json_object(latest)
    verdict = summary.get("verdict")
    return str(verdict) if verdict else None
