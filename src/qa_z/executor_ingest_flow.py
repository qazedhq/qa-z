"""Core executor-result ingest flow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
)
from qa_z.executor_ingest_checks import (
    accepted_ingest_status,
    build_freshness_check,
    build_provenance_check,
    empty_check,
    failed_check,
    next_recommendation_for_ingest,
    status_warnings_for_result,
    validation_warnings_for_result,
    verify_resume_status_for_result,
)
from qa_z.executor_ingest_bridge_warnings import (
    bridge_output_warning_ids,
    bridge_output_warning_ids_for_manifest,
    unique_warning_ids,
)
from qa_z.executor_ingest_finalize import finalize_ingest_success
from qa_z.executor_ingest_outcome import (
    executor_result_id,
    ingest_source_context,
)
from qa_z.executor_ingest_rejections import raise_rejected_ingest
from qa_z.executor_ingest_scope import validate_result_scope
from qa_z.executor_ingest_session import (
    persist_ingested_result,
    resume_verification_if_ready,
)
from qa_z.executor_ingest_support import (
    optional_text,
    resolve_relative_path,
)
from qa_z.executor_ingest_verification import verify_repair_session
from qa_z.executor_result import (
    load_bridge_manifest,
    load_executor_result,
)
from qa_z.repair_session import RepairSession, load_repair_session
from qa_z.verification import VerificationVerdict


VERIFY_READY_STATUSES = {"ready_for_verify", "ingested_with_warning"}


def ingest_executor_result_artifact(
    *,
    root: Path,
    config: dict[str, Any],
    result_path: str | Path,
    now: str | None = None,
):
    """Ingest an external executor result and optionally resume verification."""
    root = root.resolve()
    resolved_result_path = resolve_relative_path(root, result_path)
    result = load_executor_result(resolved_result_path)
    result_id = executor_result_id(result)
    warnings: list[str] = []
    stored_result_path: Path | None = None
    verification_triggered = False
    verification_verdict: VerificationVerdict | None = None
    verify_summary_path: Path | None = None
    session_id = result.source_session_id
    source_loop_id = result.source_loop_id
    bridge: dict[str, Any] | None = None
    source_context: dict[str, Any] = {}
    session: RepairSession | None = None

    try:
        bridge = load_bridge_manifest(
            root, result.bridge_id, result_path=resolved_result_path
        )
    except (ArtifactLoadError, ArtifactSourceNotFound) as exc:
        raise_rejected_ingest(
            root=root,
            session=session,
            result=result,
            result_id=result_id,
            session_id=session_id,
            source_loop_id=source_loop_id,
            ingest_status="rejected_invalid",
            warnings=warnings,
            freshness_check=empty_check(status="warning", reason="bridge_missing"),
            provenance_check=failed_check(
                reason="bridge_missing",
                details=[str(exc)],
            ),
            verify_resume_status="verify_blocked",
            freshness_reason=None,
            provenance_reason="bridge_missing",
            next_recommendation="fix executor bridge reference",
            message=str(exc),
            exit_code=4 if isinstance(exc, ArtifactSourceNotFound) else 2,
        )

    session_id = str(bridge.get("source_session_id") or result.source_session_id)
    source_loop_id = (
        optional_text(bridge.get("source_loop_id")) or result.source_loop_id
    )
    source_context = ingest_source_context(bridge)
    warnings.extend(bridge_output_warning_ids(bridge))
    warnings.extend(
        bridge_output_warning_ids_for_manifest(
            root, resolved_result_path, result.bridge_id
        )
    )
    warnings = unique_warning_ids(warnings)

    provenance_check = build_provenance_check(
        result=result,
        bridge=bridge,
        expected_session_id=session_id,
        expected_loop_id=source_loop_id,
    )
    if provenance_check["status"] == "failed":
        raise_rejected_ingest(
            root=root,
            session=session,
            result=result,
            result_id=result_id,
            session_id=session_id,
            source_loop_id=source_loop_id,
            ingest_status="rejected_mismatch",
            warnings=warnings,
            freshness_check=empty_check(status="warning", reason="not_evaluated"),
            provenance_check=provenance_check,
            verify_resume_status="mismatch_detected",
            freshness_reason=None,
            provenance_reason=str(provenance_check.get("reason") or ""),
            next_recommendation="inspect bridge and session provenance",
            message="Executor result provenance does not match the bridge contract.",
            source_context=source_context,
        )

    try:
        session = load_repair_session(root, session_id)
    except (ArtifactLoadError, ArtifactSourceNotFound) as exc:
        raise_rejected_ingest(
            root=root,
            session=session,
            result=result,
            result_id=result_id,
            session_id=session_id,
            source_loop_id=source_loop_id,
            ingest_status="rejected_invalid",
            warnings=warnings,
            freshness_check=empty_check(status="warning", reason="session_missing"),
            provenance_check=failed_check(
                reason="session_missing",
                details=[str(exc)],
            ),
            verify_resume_status="verify_blocked",
            freshness_reason=None,
            provenance_reason="session_missing",
            next_recommendation="restore the repair session before ingest",
            message=str(exc),
            exit_code=4 if isinstance(exc, ArtifactSourceNotFound) else 2,
            source_context=source_context,
        )

    try:
        validate_result_scope(root=root, bridge=bridge, result=result, session=session)
    except (ArtifactLoadError, ArtifactSourceNotFound) as exc:
        provenance_check = failed_check(
            reason="scope_validation_failed",
            details=[str(exc)],
        )
        raise_rejected_ingest(
            root=root,
            session=session,
            result=result,
            result_id=result_id,
            session_id=session_id,
            source_loop_id=source_loop_id,
            ingest_status="rejected_invalid",
            warnings=warnings,
            freshness_check=empty_check(status="warning", reason="not_evaluated"),
            provenance_check=provenance_check,
            verify_resume_status="verify_blocked",
            freshness_reason=None,
            provenance_reason="scope_validation_failed",
            next_recommendation="fix the executor result scope declaration",
            message=str(exc),
            exit_code=4 if isinstance(exc, ArtifactSourceNotFound) else 2,
            source_context=source_context,
        )

    freshness_check = build_freshness_check(
        result=result, bridge=bridge, session=session, now=now
    )
    warnings.extend(list(freshness_check.get("warnings", [])))
    freshness_reason = optional_text(freshness_check.get("reason"))
    if freshness_check["status"] == "failed":
        ingest_status = (
            "rejected_stale"
            if freshness_reason == "session_newer_than_result"
            else "rejected_invalid"
        )
        verify_resume_status = (
            "stale_result" if ingest_status == "rejected_stale" else "verify_blocked"
        )
        raise_rejected_ingest(
            root=root,
            session=session,
            result=result,
            result_id=result_id,
            session_id=session_id,
            source_loop_id=source_loop_id,
            ingest_status=ingest_status,
            warnings=warnings,
            freshness_check=freshness_check,
            provenance_check=provenance_check,
            verify_resume_status=verify_resume_status,
            freshness_reason=freshness_reason,
            provenance_reason=None,
            next_recommendation=(
                "request a fresh executor result"
                if ingest_status == "rejected_stale"
                else "fix executor result timestamps"
            ),
            message=str(
                freshness_check.get("details", ["executor result is stale"])[0]
            ),
            source_context=source_context,
        )

    warnings.extend(status_warnings_for_result(result))
    warnings.extend(validation_warnings_for_result(result))
    updated_session, stored_result_path = persist_ingested_result(
        root=root,
        session=session,
        result=result,
    )

    verify_resume_status = verify_resume_status_for_result(
        root=root,
        result=result,
        session=updated_session,
        warnings=warnings,
    )
    ingest_status = accepted_ingest_status(result.status, warnings)
    next_recommendation = next_recommendation_for_ingest(
        result=result,
        ingest_status=ingest_status,
        verify_resume_status=verify_resume_status,
    )
    (
        updated_session,
        verification_triggered,
        verification_verdict,
        verify_summary_path,
        next_recommendation,
    ) = resume_verification_if_ready(
        root=root,
        config=config,
        session=updated_session,
        result=result,
        verify_resume_status=verify_resume_status,
        next_recommendation=next_recommendation,
        verify_ready_statuses=VERIFY_READY_STATUSES,
        verify_runner=verify_repair_session,
    )

    return finalize_ingest_success(
        root=root,
        session=updated_session,
        result=result,
        result_id=result_id,
        session_id=session_id,
        source_loop_id=source_loop_id,
        ingest_status=ingest_status,
        warnings=warnings,
        freshness_check=freshness_check,
        provenance_check=provenance_check,
        verify_resume_status=verify_resume_status,
        freshness_reason=freshness_reason,
        next_recommendation=next_recommendation,
        stored_result_path=stored_result_path,
        verification_triggered=verification_triggered,
        verification_verdict=verification_verdict,
        verify_summary_path=verify_summary_path,
        source_context=source_context,
    )
