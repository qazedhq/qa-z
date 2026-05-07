"""Internal status and validation helpers for executor-ingest flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.executor_ingest_support import (
    current_utc_timestamp,
    optional_text,
    parse_timestamp,
    resolve_relative_path,
)
from qa_z.executor_result import next_recommendation_for_result
from qa_z.repair_session import RepairSession

VERIFY_BLOCKING_WARNINGS = {
    "completed_without_changed_files",
    "candidate_run_missing",
    "candidate_run_outside_repository",
    "candidate_run_fast_summary_missing",
    "baseline_run_missing",
    "baseline_run_outside_repository",
    "baseline_run_fast_summary_missing",
    "validation_summary_conflicts_with_results",
    "validation_result_command_not_declared",
}


def empty_check(*, status: str, reason: str) -> dict[str, Any]:
    """Return a stable empty check payload."""
    return {
        "status": status,
        "reason": reason,
        "details": [],
        "warnings": [],
    }


def failed_check(*, reason: str, details: list[str]) -> dict[str, Any]:
    """Return a stable failed check payload."""
    return {
        "status": "failed",
        "reason": reason,
        "details": list(details),
        "warnings": [],
    }


def build_freshness_check(
    *, result: Any, bridge: dict[str, Any], session: RepairSession, now: str | None
) -> dict[str, Any]:
    """Evaluate result freshness relative to the source bridge and session."""
    result_text = optional_text(getattr(result, "created_at", None))
    bridge_text = optional_text(bridge.get("created_at"))
    session_text = optional_text(session.updated_at)
    ingest_text = optional_text(now) or current_utc_timestamp()
    result_dt = parse_timestamp(result_text)
    bridge_dt = parse_timestamp(bridge_text)
    session_dt = parse_timestamp(session_text)
    ingest_dt = parse_timestamp(ingest_text)
    warnings: list[str] = []
    details: list[str] = []
    status = "passed"
    reason: str | None = None

    if bridge_dt is None:
        warnings.append("missing_bridge_created_at")
        details.append("Bridge created_at is missing or invalid.")
        status = "warning"
    if session_dt is None:
        warnings.append("missing_session_updated_at")
        details.append("Session updated_at is missing or invalid.")
        status = "warning"
    if result_dt is None:
        warnings.append("missing_result_created_at")
        details.append("Result created_at is missing or invalid.")
        status = "warning"
    if ingest_dt is None:
        warnings.append("missing_ingest_reference_time")
        details.append("Ingest reference time is missing or invalid.")
        status = "warning"

    if result_dt is not None and ingest_dt is not None and result_dt > ingest_dt:
        status = "failed"
        reason = "result_from_future"
        details = [
            "Executor result created_at is newer than the ingest reference time."
        ]
    elif result_dt is not None and bridge_dt is not None and result_dt < bridge_dt:
        status = "failed"
        reason = "result_before_bridge"
        details = ["Executor result created_at predates the source bridge."]
    elif (
        result_dt is not None
        and bridge_dt is not None
        and session_dt is not None
        and session_dt > bridge_dt
        and result_dt < session_dt
    ):
        status = "failed"
        reason = "session_newer_than_result"
        details = ["Repair session updated_at is newer than the executor result."]

    return {
        "status": status,
        "reason": reason,
        "details": details,
        "warnings": stable_unique_strings(warnings),
        "result_created_at": result_text,
        "bridge_created_at": bridge_text,
        "session_updated_at": session_text,
        "ingested_at": ingest_text,
    }


def build_provenance_check(
    *,
    result: Any,
    bridge: dict[str, Any],
    expected_session_id: str,
    expected_loop_id: str | None,
) -> dict[str, Any]:
    """Confirm that the result points at the correct bridge/session/loop."""
    details: list[str] = []
    bridge_id = optional_text(bridge.get("bridge_id"))
    if bridge_id != result.bridge_id:
        details.append("Executor result bridge_id does not match the bridge manifest.")
        return failed_check(reason="bridge_id_mismatch", details=details)
    if expected_session_id != result.source_session_id:
        details.append(
            "Executor result source_session_id does not match the bridge manifest."
        )
        return failed_check(reason="source_session_mismatch", details=details)
    result_loop_id = optional_text(result.source_loop_id)
    if expected_loop_id is not None and result_loop_id != expected_loop_id:
        details.append("Executor result source_loop_id does not match the bridge loop.")
        return failed_check(reason="source_loop_mismatch", details=details)
    if expected_loop_id is None and result_loop_id is not None:
        details.append("Executor result source_loop_id was set for a session bridge.")
        return failed_check(reason="unexpected_source_loop", details=details)
    return {
        "status": "passed",
        "reason": None,
        "details": [],
        "warnings": [],
    }


def status_warnings_for_result(result: Any) -> list[str]:
    """Return conservative status-quality warnings for one executor result."""
    warnings: list[str] = []
    if result.status == "completed":
        if not result.changed_files:
            warnings.append("completed_without_changed_files")
        if result.validation.status == "failed":
            warnings.append("completed_validation_failed")
    if result.status == "no_op" and not result.notes:
        warnings.append("no_op_without_explanation")
    if result.status == "not_applicable" and not result.notes:
        warnings.append("not_applicable_without_explanation")
    return warnings


def validation_warnings_for_result(result: Any) -> list[str]:
    """Return warnings when validation metadata conflicts with detailed results."""
    validation = getattr(result, "validation", None)
    if validation is None:
        return []

    warnings: list[str] = []
    commands = {
        tuple(str(part).strip() for part in command if str(part).strip())
        for command in getattr(validation, "commands", [])
        if isinstance(command, list)
    }
    results = list(getattr(validation, "results", []))
    result_statuses = {
        str(getattr(item, "status", "")).strip()
        for item in results
        if str(getattr(item, "status", "")).strip()
    }

    if results and any(
        tuple(
            str(part).strip()
            for part in getattr(item, "command", [])
            if str(part).strip()
        )
        not in commands
        for item in results
    ):
        warnings.append("validation_result_command_not_declared")

    validation_status = str(getattr(validation, "status", "")).strip()
    if results:
        if validation_status == "passed" and "failed" in result_statuses:
            warnings.append("validation_summary_conflicts_with_results")
        elif validation_status == "failed" and result_statuses == {"passed"}:
            warnings.append("validation_summary_conflicts_with_results")
        elif validation_status == "not_run":
            warnings.append("validation_summary_conflicts_with_results")
    return warnings


def verify_resume_status_for_result(
    *,
    root: Path,
    result: Any,
    session: RepairSession,
    warnings: list[str],
) -> str:
    """Return whether deterministic verification can safely resume now."""
    if result.status != "completed":
        return "verify_blocked"
    if result.verification_hint == "candidate_run":
        candidate_dir = optional_text(result.candidate_run_dir)
        if candidate_dir is None:
            warnings.append("candidate_run_missing")
            return "verify_blocked"
        candidate_path = resolve_relative_path(root, candidate_dir)
        try:
            candidate_path.relative_to(root.resolve())
        except ValueError:
            warnings.append("candidate_run_outside_repository")
            return "verify_blocked"
        if not candidate_path.exists():
            warnings.append("candidate_run_missing")
            return "verify_blocked"
        if not (candidate_path / "fast" / "summary.json").is_file():
            warnings.append("candidate_run_fast_summary_missing")
            return "verify_blocked"
    baseline_path = resolve_relative_path(root, session.baseline_run_dir)
    try:
        baseline_path.relative_to(root.resolve())
    except ValueError:
        warnings.append("baseline_run_outside_repository")
        return "verify_blocked"
    if not baseline_path.exists():
        warnings.append("baseline_run_missing")
        return "verify_blocked"
    if not (baseline_path / "fast" / "summary.json").is_file():
        warnings.append("baseline_run_fast_summary_missing")
        return "verify_blocked"
    if any(warning in VERIFY_BLOCKING_WARNINGS for warning in warnings):
        return "verify_blocked"
    if warnings:
        return "ingested_with_warning"
    return "ready_for_verify"


def accepted_ingest_status(result_status: str, warnings: list[str]) -> str:
    """Return the accepted ingest status classification."""
    if result_status == "partial":
        return "accepted_partial"
    if result_status in {"no_op", "not_applicable"}:
        return "accepted_no_op"
    if result_status == "failed":
        return "accepted_with_warning"
    if warnings:
        return "accepted_with_warning"
    return "accepted"


def next_recommendation_for_ingest(
    *, result: Any, ingest_status: str, verify_resume_status: str
) -> str:
    """Return the next recommended operator action for an ingest outcome."""
    if ingest_status == "rejected_stale":
        return "request a fresh executor result"
    if ingest_status == "rejected_mismatch":
        return "inspect bridge and session provenance"
    if ingest_status == "rejected_invalid":
        return "fix executor result artifact"
    if verify_resume_status == "verify_blocked" and result.status == "completed":
        return "inspect executor result warnings"
    return next_recommendation_for_result(result.status)


def stable_unique_strings(values: list[str]) -> list[str]:
    """Return de-duplicated strings in first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
