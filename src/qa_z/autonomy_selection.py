"""Selection-context and verification helpers for autonomy loops."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.autonomy_records import read_json_object, resolve_evidence_path
from qa_z.improvement_state import load_history_entries
from qa_z.task_selection import fallback_family_for_category

__all__ = [
    "autonomy_selection_context",
    "next_recommendations",
    "verification_observations",
]


def is_fallback_selection_task(task: dict[str, Any]) -> bool:
    """Return whether a selected task came from fallback backlog reseeding."""
    category = str(task.get("category") or "")
    return fallback_family_for_category(category) is not None


def autonomy_selection_context(selected_artifact: dict[str, Any]) -> dict[str, Any]:
    """Return live self-inspection context copied into autonomy artifacts."""
    context: dict[str, Any] = {}
    live_repository = selected_artifact.get("live_repository")
    if isinstance(live_repository, dict) and live_repository:
        context["live_repository"] = dict(live_repository)
    for key in (
        "source_self_inspection",
        "source_self_inspection_loop_id",
        "source_self_inspection_generated_at",
    ):
        value = str(selected_artifact.get(key) or "").strip()
        if value:
            context[key] = value
    return context


def with_loop_local_self_inspection_context(
    selected_artifact: dict[str, Any], *, loop_id: str, generated_at: str
) -> dict[str, Any]:
    """Point autonomy selection provenance at the loop-local self-inspection copy."""
    updated = dict(selected_artifact)
    if "source_self_inspection" in updated or "live_repository" in updated:
        updated["source_self_inspection"] = f".qa-z/loops/{loop_id}/self_inspect.json"
        updated["source_self_inspection_loop_id"] = loop_id
        updated["source_self_inspection_generated_at"] = generated_at
    return updated


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


def selection_gap_reason_for_loop(*, backlog_open_count_after_inspection: int) -> str:
    """Return a compact reason for a taskless loop."""
    if backlog_open_count_after_inspection <= 0:
        return "no_open_backlog_after_inspection"
    return "open_backlog_items_not_selected"


def blocked_no_candidate_chain_length(
    history_path: Path, *, current_state: str, current_loop_id: str | None = None
) -> int:
    """Return the trailing blocked-no-candidates chain length including this loop."""
    if current_state != "blocked_no_candidates":
        return 0
    count = 1
    for entry in reversed(load_history_entries(history_path)):
        if current_loop_id and str(entry.get("loop_id") or "") == current_loop_id:
            continue
        if str(entry.get("state") or "") != "blocked_no_candidates":
            break
        count += 1
    return count


def blocked_no_candidate_chain_loop_ids(
    history_path: Path, *, current_state: str, current_loop_id: str | None = None
) -> list[str]:
    """Return blocked loop ids in the current trailing blocked-no-candidates chain."""
    if current_state != "blocked_no_candidates":
        return []
    loop_ids: list[str] = []
    for entry in reversed(load_history_entries(history_path)):
        if current_loop_id and str(entry.get("loop_id") or "") == current_loop_id:
            continue
        if str(entry.get("state") or "") != "blocked_no_candidates":
            break
        loop_id = str(entry.get("loop_id") or "").strip()
        if loop_id:
            loop_ids.append(loop_id)
    loop_ids.reverse()
    if current_loop_id:
        loop_ids.append(current_loop_id)
    return loop_ids


def int_value(value: object) -> int:
    """Coerce numeric-looking values into deterministic integers."""
    if value is None or value is False:
        return 0
    if value is True:
        return 1
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return 0
        try:
            return int(float(text))
        except ValueError:
            return 0
    return 0
