"""Dry-run synthesis helpers for repair-session surfaces."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from qa_z.artifacts import format_path, resolve_path
from qa_z.executor_dry_run_logic import (
    build_dry_run_summary,
    operator_decision as dry_run_operator_decision,
    operator_summary as dry_run_operator_summary,
    recommended_actions as dry_run_recommended_actions_for_signals,
)
from qa_z.executor_history import (
    executor_result_dry_run_report_path,
    executor_result_history_path,
    load_executor_result_history,
)

if TYPE_CHECKING:
    from pathlib import Path

    from qa_z.repair_session import RepairSession


def load_session_dry_run_summary(
    session: "RepairSession", root: "Path"
) -> dict[str, Any] | None:
    """Load a session-local executor dry-run summary when present."""
    session_dir = resolve_path(root, session.session_dir)
    path = session_dir / "executor_results" / "dry_run_summary.json"
    if not path.is_file():
        return synthesize_session_dry_run_summary(session, root)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return synthesize_session_dry_run_summary(session, root)
    if loaded.get("kind") != "qa_z.executor_result_dry_run":
        return synthesize_session_dry_run_summary(session, root)
    return enrich_dry_run_operator_fields({**loaded, "summary_source": "materialized"})


def synthesize_session_dry_run_summary(
    session: "RepairSession", root: "Path"
) -> dict[str, Any] | None:
    """Synthesize dry-run context from session history when no summary exists."""
    session_dir = resolve_path(root, session.session_dir)
    history_path = executor_result_history_path(session_dir)
    if not history_path.is_file():
        return None
    history = load_executor_result_history(history_path, session_id=session.session_id)
    attempts = [item for item in history.get("attempts", []) if isinstance(item, dict)]
    if not attempts:
        return None
    return enrich_dry_run_operator_fields(
        {
            **build_dry_run_summary(
                session_id=session.session_id,
                history_path=format_path(history_path, root),
                report_path=format_path(
                    executor_result_dry_run_report_path(session_dir), root
                ),
                safety_package_id=safety_package_id_for_session(session, root),
                attempts=attempts,
            ),
            "summary_source": "history_fallback",
        }
    )


def safety_package_id_for_session(session: "RepairSession", root: "Path") -> str | None:
    """Return the session-local safety package id when it can be read."""
    path_text = session.safety_artifacts.get("policy_json")
    if not path_text:
        return None
    path = resolve_path(root, path_text)
    if not path.is_file():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return None
    package_id = str(loaded.get("package_id") or "").strip()
    return package_id or None


def enrich_dry_run_operator_fields(summary: dict[str, Any]) -> dict[str, Any]:
    """Backfill additive operator diagnostic fields for older dry-run summaries."""
    signals = [
        str(item) for item in summary.get("history_signals", []) if str(item).strip()
    ]
    verdict = str(summary.get("verdict") or "").strip()
    enriched = dict(summary)
    if not str(enriched.get("operator_decision") or "").strip():
        enriched["operator_decision"] = dry_run_operator_decision(verdict, signals)
    if not str(enriched.get("operator_summary") or "").strip():
        enriched["operator_summary"] = dry_run_operator_summary(verdict, signals)
    if not normalized_dry_run_actions(enriched.get("recommended_actions")):
        enriched["recommended_actions"] = dry_run_recommended_actions_for_signals(
            verdict,
            signals,
        )
    return enriched


def normalized_dry_run_actions(value: object) -> list[dict[str, str]]:
    """Normalize optional dry-run recommended actions for JSON and Markdown."""
    if not isinstance(value, list):
        return []
    actions: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action_id = str(item.get("id") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if action_id and summary:
            actions.append({"id": action_id, "summary": summary})
    return actions


def dry_run_action_summary_text(value: object) -> str:
    """Render recommended dry-run action summaries as one compact line."""
    return "; ".join(action["summary"] for action in normalized_dry_run_actions(value))
