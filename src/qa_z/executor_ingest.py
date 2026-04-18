"""Executor-result ingest and shared repair-session verification helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from qa_z.artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    RunSource,
    extract_candidate_files,
    extract_contract_candidate_files,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    write_latest_run_manifest,
)
from qa_z.autonomy import record_executor_result
from qa_z.executor_history import append_executor_result_attempt
from qa_z.config import get_nested
from qa_z.executor_result import (
    ingest_summary_dict,
    load_bridge_manifest,
    load_executor_result,
    next_recommendation_for_result,
    store_executor_result,
    write_json,
)
from qa_z.repair_session import (
    RepairSession,
    RepairSessionState,
    complete_session_verification,
    load_repair_session,
    write_session_manifest,
)
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.review_packet import (
    render_run_review_packet,
    run_review_packet_json,
    write_review_artifacts,
)
from qa_z.reporters.run_summary import write_run_summary_artifacts
from qa_z.reporters.sarif import write_sarif_artifact
from qa_z.runners.deep import run_deep
from qa_z.runners.fast import run_fast
from qa_z.runners.models import RunSummary
from qa_z.verification import (
    VerificationRun,
    VerificationVerdict,
    compare_verification_runs,
    load_verification_run,
    write_verification_artifacts,
)


@dataclass(frozen=True)
class ExecutorResultIngestOutcome:
    """Structured result for one executor-result ingest pass."""

    summary: dict[str, Any]
    verification_verdict: VerificationVerdict | None


class ExecutorResultIngestRejected(ValueError):
    """Raised when a structured executor result is recorded but not accepted."""

    def __init__(
        self,
        *,
        outcome: ExecutorResultIngestOutcome,
        message: str,
        exit_code: int = 2,
    ) -> None:
        super().__init__(message)
        self.outcome = outcome
        self.exit_code = exit_code


VERIFY_READY_STATUSES = {"ready_for_verify", "ingested_with_warning"}
VERIFY_BLOCKING_WARNINGS = {
    "completed_without_changed_files",
    "candidate_run_missing",
    "baseline_run_missing",
    "validation_summary_conflicts_with_results",
    "validation_result_command_not_declared",
}


def ingest_executor_result_artifact(
    *,
    root: Path,
    config: dict[str, Any],
    result_path: str | Path,
    now: str | None = None,
) -> ExecutorResultIngestOutcome:
    """Ingest an external executor result and optionally resume verification."""
    root = root.resolve()
    result = load_executor_result(resolve_relative_path(root, result_path))
    result_id = executor_result_id(result)
    warnings: list[str] = []
    stored_result_path: Path | None = None
    session_state: RepairSessionState | None = None
    verification_triggered = False
    verification_verdict: VerificationVerdict | None = None
    verify_summary_path: Path | None = None
    session_id = result.source_session_id
    source_loop_id = result.source_loop_id
    bridge: dict[str, Any] | None = None
    session: RepairSession | None = None

    try:
        bridge = load_bridge_manifest(root, result.bridge_id)
    except (ArtifactLoadError, ArtifactSourceNotFound) as exc:
        outcome = rejected_ingest_outcome(
            root=root,
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
            backlog_implications=backlog_implications_for_ingest(
                result=result,
                result_id=result_id,
                ingest_status="rejected_invalid",
                freshness_reason=None,
                provenance_reason="bridge_missing",
                warnings=warnings,
            ),
            next_recommendation="fix executor bridge reference",
            stored_result_path=None,
            session_state=None,
            verification_triggered=False,
            verification_verdict=None,
            verify_summary_path=None,
        )
        record_attempt_if_possible(
            root=root,
            session=session,
            result=result,
            outcome=outcome,
        )
        raise ExecutorResultIngestRejected(
            outcome=outcome,
            message=str(exc),
            exit_code=4 if isinstance(exc, ArtifactSourceNotFound) else 2,
        ) from exc

    session_id = str(bridge.get("source_session_id") or result.source_session_id)
    source_loop_id = (
        optional_text(bridge.get("source_loop_id")) or result.source_loop_id
    )

    provenance_check = build_provenance_check(
        result=result,
        bridge=bridge,
        expected_session_id=session_id,
        expected_loop_id=source_loop_id,
    )
    if provenance_check["status"] == "failed":
        outcome = rejected_ingest_outcome(
            root=root,
            result=result,
            result_id=result_id,
            session_id=session_id,
            source_loop_id=source_loop_id,
            ingest_status="rejected_mismatch",
            warnings=warnings,
            freshness_check=empty_check(status="warning", reason="not_evaluated"),
            provenance_check=provenance_check,
            verify_resume_status="mismatch_detected",
            backlog_implications=backlog_implications_for_ingest(
                result=result,
                result_id=result_id,
                ingest_status="rejected_mismatch",
                freshness_reason=None,
                provenance_reason=str(provenance_check.get("reason") or ""),
                warnings=warnings,
            ),
            next_recommendation="inspect bridge and session provenance",
            stored_result_path=None,
            session_state=None,
            verification_triggered=False,
            verification_verdict=None,
            verify_summary_path=None,
        )
        raise ExecutorResultIngestRejected(
            outcome=outcome,
            message="Executor result provenance does not match the bridge contract.",
        )

    try:
        session = load_repair_session(root, session_id)
    except (ArtifactLoadError, ArtifactSourceNotFound) as exc:
        outcome = rejected_ingest_outcome(
            root=root,
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
            backlog_implications=backlog_implications_for_ingest(
                result=result,
                result_id=result_id,
                ingest_status="rejected_invalid",
                freshness_reason=None,
                provenance_reason="session_missing",
                warnings=warnings,
            ),
            next_recommendation="restore the repair session before ingest",
            stored_result_path=None,
            session_state=None,
            verification_triggered=False,
            verification_verdict=None,
            verify_summary_path=None,
        )
        record_attempt_if_possible(
            root=root,
            session=session,
            result=result,
            outcome=outcome,
        )
        raise ExecutorResultIngestRejected(
            outcome=outcome,
            message=str(exc),
            exit_code=4 if isinstance(exc, ArtifactSourceNotFound) else 2,
        ) from exc

    try:
        validate_result_scope(root=root, bridge=bridge, result=result, session=session)
    except (ArtifactLoadError, ArtifactSourceNotFound) as exc:
        provenance_check = failed_check(
            reason="scope_validation_failed",
            details=[str(exc)],
        )
        outcome = rejected_ingest_outcome(
            root=root,
            result=result,
            result_id=result_id,
            session_id=session_id,
            source_loop_id=source_loop_id,
            ingest_status="rejected_invalid",
            warnings=warnings,
            freshness_check=empty_check(status="warning", reason="not_evaluated"),
            provenance_check=provenance_check,
            verify_resume_status="verify_blocked",
            backlog_implications=backlog_implications_for_ingest(
                result=result,
                result_id=result_id,
                ingest_status="rejected_invalid",
                freshness_reason=None,
                provenance_reason="scope_validation_failed",
                warnings=warnings,
            ),
            next_recommendation="fix the executor result scope declaration",
            stored_result_path=None,
            session_state=None,
            verification_triggered=False,
            verification_verdict=None,
            verify_summary_path=None,
        )
        record_attempt_if_possible(
            root=root,
            session=session,
            result=result,
            outcome=outcome,
        )
        raise ExecutorResultIngestRejected(
            outcome=outcome,
            message=str(exc),
            exit_code=4 if isinstance(exc, ArtifactSourceNotFound) else 2,
        ) from exc

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
                provenance_reason=None,
                warnings=warnings,
            ),
            next_recommendation=(
                "request a fresh executor result"
                if ingest_status == "rejected_stale"
                else "fix executor result timestamps"
            ),
            stored_result_path=None,
            session_state=None,
            verification_triggered=False,
            verification_verdict=None,
            verify_summary_path=None,
        )
        record_attempt_if_possible(
            root=root,
            session=session,
            result=result,
            outcome=outcome,
        )
        raise ExecutorResultIngestRejected(
            outcome=outcome,
            message=str(
                freshness_check.get("details", ["executor result is stale"])[0]
            ),
        )

    warnings.extend(status_warnings_for_result(result))
    warnings.extend(validation_warnings_for_result(result))
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

    if (
        verify_resume_status in VERIFY_READY_STATUSES
        and result.verification_hint == "rerun"
    ):
        updated_session, verification_summary, comparison = verify_repair_session(
            session=updated_session,
            root=root,
            config=config,
            candidate_run=None,
            rerun=True,
            rerun_output_dir=None,
            strict_no_tests=False,
            output_dir=None,
        )
        verification_triggered = True
        verification_verdict = comparison.verdict
        verify_summary_path = (
            resolve_relative_path(root, verification_summary["verify_dir"])
            / "summary.json"
        )
        next_recommendation = verification_summary["next_recommendation"]
    elif (
        verify_resume_status in VERIFY_READY_STATUSES
        and result.verification_hint == "candidate_run"
    ):
        updated_session, verification_summary, comparison = verify_repair_session(
            session=updated_session,
            root=root,
            config=config,
            candidate_run=result.candidate_run_dir,
            rerun=False,
            rerun_output_dir=None,
            strict_no_tests=False,
            output_dir=None,
        )
        verification_triggered = True
        verification_verdict = comparison.verdict
        verify_summary_path = (
            resolve_relative_path(root, verification_summary["verify_dir"])
            / "summary.json"
        )
        next_recommendation = verification_summary["next_recommendation"]

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
        session_state=updated_session.state,
        verification_triggered=verification_triggered,
        verification_verdict=verification_verdict,
        verify_summary_path=verify_summary_path,
    )
    record_attempt_if_possible(
        root=root,
        session=updated_session,
        result=result,
        outcome=outcome,
    )

    if source_loop_id:
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
    return outcome


def verify_repair_session(
    *,
    session: RepairSession,
    root: Path,
    config: dict[str, Any],
    candidate_run: str | None,
    rerun: bool,
    rerun_output_dir: str | None,
    strict_no_tests: bool,
    output_dir: str | None,
) -> tuple[RepairSession, dict[str, Any], Any]:
    """Run the shared repair-session verification flow."""
    baseline, _baseline_source = load_verification_run(
        root=root,
        config=config,
        from_run=session.baseline_run_dir,
    )
    if rerun:
        session_dir = resolve_relative_path(root, session.session_dir)
        resolved_rerun_output_dir = (
            resolve_relative_path(root, rerun_output_dir)
            if rerun_output_dir
            else session_dir / "candidate"
        )
        resolved_candidate_run = create_verify_candidate_run(
            root=root,
            config=config,
            rerun_output_dir=resolved_rerun_output_dir,
            strict_no_tests=strict_no_tests,
            baseline=baseline,
        )
    else:
        if candidate_run is None:
            raise ValueError("candidate_run is required when rerun is not requested.")
        resolved_candidate_run = candidate_run

    candidate, candidate_source = load_verification_run(
        root=root,
        config=config,
        from_run=resolved_candidate_run,
    )
    comparison = compare_verification_runs(baseline, candidate)
    resolved_output_dir = (
        resolve_relative_path(root, output_dir)
        if output_dir
        else resolve_relative_path(root, session.session_dir) / "verify"
    )
    paths = write_verification_artifacts(comparison, resolved_output_dir)
    updated, summary = complete_session_verification(
        session=session,
        root=root,
        candidate_run_dir=candidate_source.run_dir,
        verify_paths=paths,
        comparison=comparison,
    )
    return updated, summary, comparison


def create_verify_candidate_run(
    *,
    root: Path,
    config: dict[str, Any],
    rerun_output_dir: Path,
    strict_no_tests: bool,
    baseline: VerificationRun,
) -> str:
    """Run fast and deep checks to create candidate evidence for verification."""
    contract_path = None
    if baseline.fast_summary.contract_path:
        candidate_contract = resolve_relative_path(
            root, baseline.fast_summary.contract_path
        )
        if candidate_contract.is_file():
            contract_path = candidate_contract

    fast_run = run_fast(
        root=root,
        config=config,
        contract_path=contract_path,
        output_dir=rerun_output_dir,
        strict_no_tests=strict_no_tests,
        selection_mode=resolve_fast_selection_mode(config),
    )
    artifact_dir = Path(fast_run.summary.artifact_dir or "")
    if not artifact_dir.is_absolute():
        artifact_dir = root / artifact_dir
    summary_path = write_run_summary_artifacts(fast_run.summary, artifact_dir)
    run_dir = artifact_dir.parent
    write_latest_run_manifest(root, config, run_dir)

    deep_run = run_deep(
        root=root,
        config=config,
        from_run=str(run_dir),
        selection_mode=resolve_deep_selection_mode(config),
    )
    write_run_summary_artifacts(deep_run.summary, deep_run.resolution.deep_dir)
    write_sarif_artifact(
        deep_run.summary, deep_run.resolution.deep_dir / "results.sarif"
    )
    candidate_source = RunSource(
        run_dir=run_dir,
        fast_dir=summary_path.parent,
        summary_path=summary_path,
    )
    write_verify_rerun_review_artifacts(
        root=root,
        config=config,
        run_source=candidate_source,
        summary=load_run_summary(summary_path),
        deep_summary=load_sibling_deep_summary(candidate_source) or deep_run.summary,
    )
    return format_relative_path(run_dir, root)


def write_verify_rerun_review_artifacts(
    *,
    root: Path,
    config: dict[str, Any],
    run_source: RunSource,
    summary: RunSummary,
    deep_summary: RunSummary,
) -> None:
    """Write run-aware review artifacts for a freshly rerun candidate."""
    contract_path = resolve_contract_source(root, config, summary=summary)
    contract = load_contract_context(contract_path, root)
    markdown = render_run_review_packet(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    json_text = run_review_packet_json(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    write_review_artifacts(markdown, json_text, run_source.run_dir / "review")


def record_attempt_if_possible(
    *,
    root: Path,
    session: RepairSession | None,
    result: Any,
    outcome: ExecutorResultIngestOutcome,
) -> None:
    """Append a readable executor-result attempt when a session is available."""
    if session is None:
        return
    append_executor_result_attempt(
        root=root,
        session_dir=resolve_relative_path(root, session.session_dir),
        session_id=session.session_id,
        result_payload=result.to_dict(),
        ingest_summary=outcome.summary,
    )


def finalized_ingest_outcome(
    *,
    root: Path,
    result: Any,
    result_id: str,
    session_id: str,
    source_loop_id: str | None,
    ingest_status: str,
    warnings: list[str],
    freshness_check: dict[str, Any],
    provenance_check: dict[str, Any],
    verify_resume_status: str,
    backlog_implications: list[dict[str, Any]],
    next_recommendation: str,
    stored_result_path: Path | None,
    session_state: str | None,
    verification_triggered: bool,
    verification_verdict: VerificationVerdict | None,
    verify_summary_path: Path | None,
) -> ExecutorResultIngestOutcome:
    """Write the ingest summary and Markdown report for one result."""
    ingest_dir = root / ".qa-z" / "executor-results" / result_id
    ingest_artifact_path = ingest_dir / "ingest.json"
    ingest_report_path = ingest_dir / "ingest_report.md"
    summary = ingest_summary_dict(
        result_id=result_id,
        bridge_id=result.bridge_id,
        session_id=session_id,
        source_loop_id=source_loop_id,
        result_status=result.status,
        ingest_status=ingest_status,
        stored_result_path=stored_result_path,
        root=root,
        session_state=session_state,
        verification_hint=result.verification_hint,
        verification_triggered=verification_triggered,
        verification_verdict=verification_verdict,
        verify_summary_path=verify_summary_path,
        warnings=stable_unique_strings(warnings),
        freshness_check=freshness_check,
        provenance_check=provenance_check,
        verify_resume_status=verify_resume_status,
        backlog_implications=backlog_implications,
        next_recommendation=next_recommendation,
        ingest_artifact_path=ingest_artifact_path,
        ingest_report_path=ingest_report_path,
    )
    write_json(ingest_artifact_path, summary)
    ingest_report_path.parent.mkdir(parents=True, exist_ok=True)
    ingest_report_path.write_text(render_ingest_report(summary), encoding="utf-8")
    return ExecutorResultIngestOutcome(
        summary=summary,
        verification_verdict=verification_verdict,
    )


def rejected_ingest_outcome(
    *,
    root: Path,
    result: Any,
    result_id: str,
    session_id: str,
    source_loop_id: str | None,
    ingest_status: str,
    warnings: list[str],
    freshness_check: dict[str, Any],
    provenance_check: dict[str, Any],
    verify_resume_status: str,
    backlog_implications: list[dict[str, Any]],
    next_recommendation: str,
    stored_result_path: Path | None,
    session_state: str | None,
    verification_triggered: bool,
    verification_verdict: VerificationVerdict | None,
    verify_summary_path: Path | None,
) -> ExecutorResultIngestOutcome:
    """Create a stored rejection outcome for machine consumers."""
    return finalized_ingest_outcome(
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
        session_state=session_state,
        verification_triggered=verification_triggered,
        verification_verdict=verification_verdict,
        verify_summary_path=verify_summary_path,
    )


def executor_result_id(result: Any) -> str:
    """Create a stable executor-result ingest record id."""
    timestamp = compact_timestamp(optional_text(getattr(result, "created_at", None)))
    return f"{slugify(str(getattr(result, 'bridge_id', 'bridge')))}-{timestamp}"


def compact_timestamp(value: str | None) -> str:
    """Collapse a timestamp into a safe compact token."""
    text = value or "unknown"
    compact = "".join(character.lower() for character in text if character.isalnum())
    return compact or "unknown"


def slugify(value: str) -> str:
    """Create a stable identifier fragment."""
    cleaned = "".join(
        character.lower() if character.isalnum() else "-" for character in value.strip()
    )
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "unknown"


def optional_text(value: object) -> str | None:
    """Return stripped text or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_timestamp(value: str | None) -> datetime | None:
    """Parse a UTC-ish timestamp conservatively."""
    text = optional_text(value)
    if text is None:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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
        if (
            candidate_dir is None
            or not resolve_relative_path(root, candidate_dir).exists()
        ):
            warnings.append("candidate_run_missing")
            return "verify_blocked"
    if not resolve_relative_path(root, session.baseline_run_dir).exists():
        warnings.append("baseline_run_missing")
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


def backlog_implications_for_ingest(
    *,
    result: Any,
    result_id: str,
    ingest_status: str,
    freshness_reason: str | None,
    provenance_reason: str | None,
    warnings: list[str],
) -> list[dict[str, Any]]:
    """Translate ingest outcomes into structural backlog implications."""
    items: list[dict[str, Any]] = []
    if (
        freshness_reason
        in {
            "session_newer_than_result",
            "result_before_bridge",
            "result_from_future",
        }
        or ingest_status == "rejected_stale"
    ):
        items.append(
            backlog_implication(
                implication_id=f"evidence_freshness_gap-{result_id}",
                title="Harden executor result freshness handling",
                category="evidence_freshness_gap",
                recommendation="harden_executor_result_freshness",
                signals=["executor_result_stale"],
                impact=3,
                likelihood=4,
                confidence=4,
                repair_cost=3,
                summary="timestamp ordering blocked verification resume",
            )
        )
    if ingest_status == "rejected_mismatch" or provenance_reason:
        items.append(
            backlog_implication(
                implication_id=f"provenance_gap-{result_id}",
                title="Harden executor provenance validation",
                category="provenance_gap",
                recommendation="audit_executor_contract",
                signals=["executor_result_provenance_mismatch"],
                impact=4,
                likelihood=4,
                confidence=4,
                repair_cost=3,
                summary="bridge/session provenance mismatch rejected ingest",
            )
        )
    if ingest_status == "accepted_partial":
        items.append(
            backlog_implication(
                implication_id=f"partial_completion_gap-{result_id}",
                title="Harden partial completion ingest handling",
                category="partial_completion_gap",
                recommendation="harden_partial_completion_handling",
                signals=["executor_result_partial"],
                impact=3,
                likelihood=4,
                confidence=4,
                repair_cost=3,
                summary="partial result blocked immediate verify",
            )
        )
    if result.status in {"no_op", "not_applicable"} or (
        "completed_without_changed_files" in warnings
        or "no_op_without_explanation" in warnings
    ):
        items.append(
            backlog_implication(
                implication_id=f"no_op_safeguard_gap-{result_id}",
                title="Harden no-op executor result safeguards",
                category="no_op_safeguard_gap",
                recommendation="harden_executor_no_op_safeguards",
                signals=["executor_result_no_op"],
                impact=3,
                likelihood=3,
                confidence=4,
                repair_cost=2,
                summary="no-op style result lacked a strong explanation or file trace",
            )
        )
    if {
        "validation_summary_conflicts_with_results",
        "validation_result_command_not_declared",
    } & set(warnings):
        items.append(
            backlog_implication(
                implication_id=f"workflow_gap-{result_id}",
                title="Harden executor validation evidence consistency",
                category="workflow_gap",
                recommendation="audit_executor_contract",
                signals=["executor_validation_failed"],
                impact=3,
                likelihood=3,
                confidence=4,
                repair_cost=2,
                summary="validation metadata conflicted with detailed executor results",
            )
        )
    return unique_implications(items)


def backlog_implication(
    *,
    implication_id: str,
    title: str,
    category: str,
    recommendation: str,
    signals: list[str],
    impact: int,
    likelihood: int,
    confidence: int,
    repair_cost: int,
    summary: str,
) -> dict[str, Any]:
    """Build one structured backlog implication entry."""
    return {
        "id": implication_id,
        "title": title,
        "category": category,
        "recommendation": recommendation,
        "signals": list(signals),
        "impact": impact,
        "likelihood": likelihood,
        "confidence": confidence,
        "repair_cost": repair_cost,
        "summary": summary,
    }


def unique_implications(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate implication entries by id."""
    seen: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = str(item.get("id") or "")
        if item_id and item_id not in seen:
            seen[item_id] = item
    return [seen[key] for key in sorted(seen)]


def stable_unique_strings(values: list[str]) -> list[str]:
    """Return de-duplicated strings in first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def current_utc_timestamp() -> str:
    """Return a stable UTC timestamp string for ingest bookkeeping."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def render_ingest_report(summary: dict[str, Any]) -> str:
    """Render a human-readable executor-result ingest report."""
    lines = [
        "# QA-Z Executor Result Ingest Report",
        "",
        f"- Result id: `{summary.get('result_id')}`",
        f"- Ingest status: `{summary.get('ingest_status')}`",
        f"- Result status: `{summary.get('result_status')}`",
        f"- Bridge: `{summary.get('bridge_id')}`",
        f"- Session: `{summary.get('session_id')}`",
        f"- Verify resume: `{summary.get('verify_resume_status')}`",
        f"- Verification: `{summary.get('verification_verdict') or 'not_run'}`",
        f"- Next: {summary.get('next_recommendation')}",
        "",
        "## Warnings",
        "",
    ]
    warnings = summary.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(f"- `{warning}`" for warning in warnings)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Freshness",
            "",
            f"- Status: `{summary.get('freshness_check', {}).get('status', 'unknown')}`",
        ]
    )
    lines.extend(
        f"- {detail}"
        for detail in summary.get("freshness_check", {}).get("details", [])
        if str(detail).strip()
    )
    lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- Status: `{summary.get('provenance_check', {}).get('status', 'unknown')}`",
        ]
    )
    lines.extend(
        f"- {detail}"
        for detail in summary.get("provenance_check", {}).get("details", [])
        if str(detail).strip()
    )
    lines.extend(["", "## Backlog Implications", ""])
    implications = summary.get("backlog_implications")
    if isinstance(implications, list) and implications:
        for item in implications:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('category', 'workflow_gap')}`: {item.get('summary', '')}"
            )
    else:
        lines.append("- none")
    return "\n".join(lines).strip() + "\n"


def resolve_relative_path(root: Path, value: str | Path) -> Path:
    """Resolve a path relative to the repository root when needed."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def format_relative_path(path: Path, root: Path) -> str:
    """Return a slash-separated path relative to root when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_fast_selection_mode(config: dict[str, Any]) -> str:
    """Resolve the configured fast selection mode."""
    configured = str(
        get_nested(config, "fast", "selection", "default_mode", default="full")
    )
    return configured if configured in {"full", "smart"} else "full"


def resolve_deep_selection_mode(config: dict[str, Any]) -> str:
    """Resolve the configured deep selection mode."""
    configured = str(
        get_nested(config, "deep", "selection", "default_mode", default="full")
    )
    return configured if configured in {"full", "smart"} else "full"


def validate_result_scope(
    *,
    root: Path,
    bridge: dict[str, Any],
    result: Any,
    session: RepairSession | None = None,
) -> None:
    """Reject executor results that report unrelated changed files."""
    allowed_files = bridge_allowed_files(root=root, bridge=bridge, session=session)
    if not allowed_files and not result.changed_files:
        return
    if not allowed_files:
        raise ArtifactLoadError(
            "Executor bridge affected_files are missing, so changed_files cannot be validated."
        )
    unexpected = unexpected_changed_files(
        changed_files=result.changed_files,
        allowed_files=allowed_files,
    )
    if unexpected:
        raise ArtifactLoadError(
            "Executor result changed_files are outside the bridge affected_files: "
            + ", ".join(unexpected)
        )


def bridge_allowed_files(
    *, root: Path, bridge: dict[str, Any], session: RepairSession | None = None
) -> set[str]:
    """Return the allowed changed files declared by the bridge handoff."""
    handoff_path_text = str(bridge.get("handoff_path") or "").strip()
    if not handoff_path_text:
        inputs = bridge.get("inputs")
        if isinstance(inputs, dict):
            handoff_path_text = str(inputs.get("handoff") or "").strip()
    if not handoff_path_text:
        raise ArtifactLoadError(
            "Executor bridge is missing handoff_path required for scope validation."
        )
    handoff = read_json_object(resolve_relative_path(root, handoff_path_text))
    repair = handoff.get("repair")
    if not isinstance(repair, dict):
        raise ArtifactLoadError("Executor bridge handoff is missing repair scope.")
    allowed = {
        normalize_repo_path(str(path))
        for path in repair.get("affected_files", [])
        if str(path).strip()
    }
    targets = repair.get("targets")
    if isinstance(targets, list):
        for target in targets:
            if not isinstance(target, dict):
                continue
            for path in target.get("affected_files", []):
                text = str(path).strip()
                if text:
                    allowed.add(normalize_repo_path(text))
    if not allowed and session is not None:
        contract_path_text = optional_text(session.provenance.get("contract_path"))
        if contract_path_text:
            contract = load_contract_context(
                resolve_relative_path(root, contract_path_text), root
            )
            allowed.update(
                normalize_repo_path(path)
                for path in extract_contract_candidate_files(contract)
            )
            if not allowed:
                allowed.update(
                    normalize_repo_path(path)
                    for path in extract_candidate_files(contract.raw_markdown)
                )
    return allowed


def unexpected_changed_files(
    *, changed_files: list[Any], allowed_files: set[str]
) -> list[str]:
    """Return changed file paths that fall outside the allowed bridge scope."""
    unexpected: list[str] = []
    for changed in changed_files:
        path = normalize_repo_path(str(getattr(changed, "path", "") or ""))
        old_path = normalize_repo_path(str(getattr(changed, "old_path", "") or ""))
        if path and path in allowed_files:
            continue
        if old_path and old_path in allowed_files:
            continue
        if path:
            unexpected.append(path)
    return unexpected


def normalize_repo_path(value: str) -> str:
    """Normalize a repository-relative path to slash-separated text."""
    return value.replace("\\", "/").strip().strip("/")


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a required JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactLoadError(
            f"Could not read executor-ingest artifact: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(
            f"Executor-ingest artifact is not valid JSON: {path}"
        ) from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError(f"Executor-ingest artifact must be an object: {path}")
    return data
