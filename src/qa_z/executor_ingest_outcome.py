"""Outcome helpers for executor-result ingest flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.executor_history import append_executor_result_attempt
from qa_z.executor_ingest_backlog import stable_unique_strings
from qa_z.executor_result import ingest_summary_dict, write_json
from qa_z.verification_models import VerificationVerdict


def record_attempt_if_possible(
    *,
    root: Path,
    session: object | None,
    result: Any,
    outcome: object,
) -> None:
    """Append a readable executor-result attempt when a session is available."""
    if session is None:
        return
    append_executor_result_attempt(
        root=root,
        session_dir=Path(root / str(getattr(session, "session_dir"))).resolve(),
        session_id=str(getattr(session, "session_id")),
        result_payload=result.to_dict(),
        ingest_summary=dict(getattr(outcome, "summary")),
    )


def ingest_source_context(bridge: dict[str, Any] | None) -> dict[str, Any]:
    """Return source self-inspection context copied from a bridge manifest."""
    if not bridge:
        return {}
    context: dict[str, Any] = {}
    live_repository = bridge.get("live_repository")
    if isinstance(live_repository, dict) and live_repository:
        context["live_repository"] = dict(live_repository)
    for key in (
        "source_self_inspection",
        "source_self_inspection_loop_id",
        "source_self_inspection_generated_at",
    ):
        value = _optional_text(bridge.get(key))
        if value:
            context[key] = value
    return context


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
    source_context: dict[str, Any] | None = None,
):
    """Write the ingest summary and Markdown report for one result."""
    from qa_z.executor_ingest import ExecutorResultIngestOutcome
    from qa_z.executor_ingest_render import render_ingest_report

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
        verification_verdict=_optional_text(verification_verdict),
        verify_summary_path=verify_summary_path,
        warnings=stable_unique_strings(warnings),
        freshness_check=freshness_check,
        provenance_check=provenance_check,
        verify_resume_status=verify_resume_status,
        backlog_implications=backlog_implications,
        next_recommendation=next_recommendation,
        ingest_artifact_path=ingest_artifact_path,
        ingest_report_path=ingest_report_path,
        source_self_inspection=(
            str(source_context.get("source_self_inspection"))
            if source_context and source_context.get("source_self_inspection")
            else None
        ),
        source_self_inspection_loop_id=(
            str(source_context.get("source_self_inspection_loop_id"))
            if source_context and source_context.get("source_self_inspection_loop_id")
            else None
        ),
        source_self_inspection_generated_at=(
            str(source_context.get("source_self_inspection_generated_at"))
            if source_context
            and source_context.get("source_self_inspection_generated_at")
            else None
        ),
        live_repository=(
            source_context.get("live_repository")
            if source_context
            and isinstance(source_context.get("live_repository"), dict)
            and source_context.get("live_repository")
            else None
        ),
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
    source_context: dict[str, Any] | None = None,
):
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
        source_context=source_context,
    )


def executor_result_id(result: Any) -> str:
    """Create a stable executor-result ingest record id."""
    timestamp = compact_timestamp(_optional_text(getattr(result, "created_at", None)))
    return f"{_slugify(str(getattr(result, 'bridge_id', 'bridge')))}-{timestamp}"


def compact_timestamp(value: str | None) -> str:
    """Collapse a timestamp into a safe compact token."""
    text = value or "unknown"
    compact = "".join(character.lower() for character in text if character.isalnum())
    return compact or "unknown"


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _slugify(value: str) -> str:
    cleaned = "".join(
        character.lower() if character.isalnum() else "-" for character in value.strip()
    )
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "unknown"
