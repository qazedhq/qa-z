"""Summary helpers for executor-result ingest output."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.executor_result_models import (
    EXECUTOR_RESULT_INGEST_KIND,
    EXECUTOR_RESULT_SCHEMA_VERSION,
)


def ingest_summary_dict(
    *,
    result_id: str,
    bridge_id: str,
    session_id: str,
    source_loop_id: str | None,
    result_status: str,
    ingest_status: str,
    stored_result_path: Path | None,
    root: Path,
    session_state: str | None,
    verification_hint: str,
    verification_triggered: bool,
    verification_verdict: str | None,
    verify_summary_path: Path | None,
    warnings: list[str],
    freshness_check: dict[str, Any],
    provenance_check: dict[str, Any],
    verify_resume_status: str,
    backlog_implications: list[dict[str, Any]],
    next_recommendation: str,
    ingest_artifact_path: Path,
    ingest_report_path: Path,
    source_self_inspection: str | None = None,
    source_self_inspection_loop_id: str | None = None,
    source_self_inspection_generated_at: str | None = None,
    live_repository: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build CLI JSON output for executor result ingestion."""
    summary = {
        "kind": EXECUTOR_RESULT_INGEST_KIND,
        "schema_version": EXECUTOR_RESULT_SCHEMA_VERSION,
        "result_id": result_id,
        "bridge_id": bridge_id,
        "session_id": session_id,
        "source_loop_id": source_loop_id,
        "result_status": result_status,
        "ingest_status": ingest_status,
        "stored_result_path": (
            format_path(stored_result_path, root) if stored_result_path else None
        ),
        "session_state": session_state,
        "verification_hint": verification_hint,
        "verification_triggered": verification_triggered,
        "verification_verdict": verification_verdict,
        "verify_summary_path": (
            format_path(verify_summary_path, root) if verify_summary_path else None
        ),
        "warnings": list(warnings),
        "freshness_check": dict(freshness_check),
        "provenance_check": dict(provenance_check),
        "verify_resume_status": verify_resume_status,
        "backlog_implications": list(backlog_implications),
        "next_recommendation": next_recommendation,
        "ingest_artifact_path": format_path(ingest_artifact_path, root),
        "ingest_report_path": format_path(ingest_report_path, root),
    }
    if source_self_inspection:
        summary["source_self_inspection"] = source_self_inspection
    if source_self_inspection_loop_id:
        summary["source_self_inspection_loop_id"] = source_self_inspection_loop_id
    if source_self_inspection_generated_at:
        summary["source_self_inspection_generated_at"] = (
            source_self_inspection_generated_at
        )
    if isinstance(live_repository, dict) and live_repository:
        summary["live_repository"] = dict(live_repository)
    return summary


def next_recommendation_for_result(status: str) -> str:
    """Return a deterministic recommendation when verification is skipped."""
    if status == "completed":
        return "run repair-session verify"
    if status == "no_op":
        return "inspect no-op result"
    if status == "not_applicable":
        return "confirm task applicability"
    if status == "failed":
        return "triage executor failure"
    return "continue repair"
