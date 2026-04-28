"""Rejection helpers for executor-result ingest flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any, NoReturn

from qa_z.executor_ingest_backlog import backlog_implications_for_ingest
from qa_z.executor_ingest_outcome import (
    record_attempt_if_possible,
    rejected_ingest_outcome,
)


def raise_rejected_ingest(
    *,
    root: Path,
    session: object | None,
    result: Any,
    result_id: str,
    session_id: str,
    source_loop_id: str | None,
    ingest_status: str,
    warnings: list[str],
    freshness_check: dict[str, Any],
    provenance_check: dict[str, Any],
    verify_resume_status: str,
    freshness_reason: str | None,
    provenance_reason: str | None,
    next_recommendation: str,
    message: str,
    exit_code: int = 2,
    source_context: dict[str, Any] | None = None,
) -> NoReturn:
    """Persist a rejected ingest outcome and raise a structured exception."""
    from qa_z.executor_ingest import ExecutorResultIngestRejected

    outcome = rejected_ingest_outcome(
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
        backlog_implications=backlog_implications_for_ingest(
            result=result,
            result_id=result_id,
            ingest_status=ingest_status,
            freshness_reason=freshness_reason,
            provenance_reason=provenance_reason,
            warnings=warnings,
        ),
        next_recommendation=next_recommendation,
        stored_result_path=None,
        session_state=None,
        verification_triggered=False,
        verification_verdict=None,
        verify_summary_path=None,
        source_context=source_context,
    )
    record_attempt_if_possible(
        root=root,
        session=session,
        result=result,
        outcome=outcome,
    )
    raise ExecutorResultIngestRejected(
        outcome=outcome,
        message=message,
        exit_code=exit_code,
    )
