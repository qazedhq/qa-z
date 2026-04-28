"""Session persistence and verify-resume helpers for executor-ingest flows."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable, cast

from qa_z.autonomy import record_executor_result
from qa_z.executor_ingest_support import format_relative_path, resolve_relative_path
from qa_z.executor_result import store_executor_result
from qa_z.repair_session import (
    RepairSession,
    RepairSessionState,
    write_session_manifest,
)
from qa_z.verification import VerificationVerdict

VerifyRunner = Callable[..., tuple[RepairSession, dict[str, Any], Any]]


def persist_ingested_result(
    *,
    root: Path,
    session: RepairSession,
    result: Any,
) -> tuple[RepairSession, Path]:
    """Store an ingested result and update the owning repair-session manifest."""
    session_dir = resolve_relative_path(root, session.session_dir)
    stored_result_path = store_executor_result(root, session_dir, result)
    session_state = cast(
        RepairSessionState,
        "failed" if result.status == "failed" else "candidate_generated",
    )
    updated_session = replace(
        session,
        state=session_state,
        updated_at=result.created_at,
        executor_result_path=format_relative_path(stored_result_path, root),
        executor_result_status=result.status,
        executor_result_validation_status=result.validation.status,
        executor_result_bridge_id=result.bridge_id,
    )
    write_session_manifest(updated_session, root)
    return updated_session, stored_result_path


def resume_verification_if_ready(
    *,
    root: Path,
    config: dict[str, Any],
    session: RepairSession,
    result: Any,
    verify_resume_status: str,
    next_recommendation: str,
    verify_ready_statuses: set[str],
    verify_runner: VerifyRunner,
) -> tuple[RepairSession, bool, VerificationVerdict | None, Path | None, str]:
    """Resume verification when ingest status and hint permit deterministic verify."""
    if verify_resume_status not in verify_ready_statuses:
        return session, False, None, None, next_recommendation

    if result.verification_hint == "rerun":
        updated_session, verification_summary, comparison = verify_runner(
            session=session,
            root=root,
            config=config,
            candidate_run=None,
            rerun=True,
            rerun_output_dir=None,
            strict_no_tests=False,
            output_dir=None,
        )
    elif result.verification_hint == "candidate_run":
        updated_session, verification_summary, comparison = verify_runner(
            session=session,
            root=root,
            config=config,
            candidate_run=result.candidate_run_dir,
            rerun=False,
            rerun_output_dir=None,
            strict_no_tests=False,
            output_dir=None,
        )
    else:
        return session, False, None, None, next_recommendation

    verify_summary_path = (
        resolve_relative_path(root, verification_summary["verify_dir"]) / "summary.json"
    )
    return (
        updated_session,
        True,
        comparison.verdict,
        verify_summary_path,
        str(verification_summary["next_recommendation"]),
    )


def record_loop_executor_result(
    *,
    root: Path,
    source_loop_id: str | None,
    result: Any,
    ingest_status: str,
    verify_resume_status: str,
    stored_result_path: Path | None,
    verification_verdict: VerificationVerdict | None,
    next_recommendation: str,
) -> None:
    """Merge executor-result ingest fields back into the matching loop history."""
    if not source_loop_id or stored_result_path is None:
        return
    record_executor_result(
        root / ".qa-z" / "loops" / "history.jsonl",
        loop_id=str(source_loop_id),
        result_status=result.status,
        ingest_status=ingest_status,
        verify_resume_status=verify_resume_status,
        result_path=format_relative_path(stored_result_path, root),
        validation_status=result.validation.status,
        changed_files=[item.path for item in result.changed_files],
        verification_hint=result.verification_hint,
        verification_verdict=verification_verdict,
        next_recommendation=next_recommendation,
    )
