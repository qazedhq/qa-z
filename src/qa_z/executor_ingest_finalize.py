"""Success-path finalize helpers for executor-result ingest flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.executor_ingest_backlog import backlog_implications_for_ingest
from qa_z.executor_ingest_outcome import (
    finalized_ingest_outcome,
    record_attempt_if_possible,
)
from qa_z.executor_ingest_session import record_loop_executor_result
from qa_z.verification_models import VerificationVerdict


def finalize_ingest_success(
    *,
    root: Path,
    session: object,
    result: Any,
    result_id: str,
    session_id: str,
    source_loop_id: str | None,
    ingest_status: str,
    warnings: list[str],
    freshness_check: dict[str, Any],
    provenance_check: dict[str, Any],
    freshness_reason: str | None,
    verify_resume_status: str,
    next_recommendation: str,
    stored_result_path: Path | None,
    verification_triggered: bool,
    verification_verdict: VerificationVerdict | None,
    verify_summary_path: Path | None,
    source_context: dict[str, Any] | None = None,
):
    """Persist success-path ingest artifacts and merge loop bookkeeping."""
    backlog_implications = backlog_implications_for_ingest(
        result=result,
        result_id=result_id,
        ingest_status=ingest_status,
        freshness_reason=freshness_reason,
        provenance_reason=None,
        warnings=warnings,
    )

    outcome = finalized_ingest_outcome(
        root=root,
        result=result,
        result_id=result_id,
        session_id=session_id,
        source_loop_id=source_loop_id,
        ingest_status=ingest_status,
        warnings=warnings,
        freshness_check=freshness_check,
        provenance_check=provenance_check,
        verify_resume_status=verify_resume_status,
        backlog_implications=backlog_implications,
        next_recommendation=next_recommendation,
        stored_result_path=stored_result_path,
        session_state=getattr(session, "state"),
        verification_triggered=verification_triggered,
        verification_verdict=verification_verdict,
        verify_summary_path=verify_summary_path,
        source_context=source_context,
    )
    record_attempt_if_possible(
        root=root,
        session=session,
        result=result,
        outcome=outcome,
    )
    record_loop_executor_result(
        root=root,
        source_loop_id=source_loop_id,
        result=result,
        ingest_status=ingest_status,
        verify_resume_status=verify_resume_status,
        stored_result_path=stored_result_path,
        verification_verdict=verification_verdict,
        next_recommendation=next_recommendation,
    )
    return outcome
