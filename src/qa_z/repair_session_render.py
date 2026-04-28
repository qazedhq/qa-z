"""Repair-session rendering helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qa_z.repair_session_dry_run import normalized_dry_run_actions

if TYPE_CHECKING:
    from qa_z.repair_session import RepairSession


def render_session_status(session: RepairSession) -> str:
    """Render current session state for human CLI output."""
    return render_session_status_with_dry_run(session, dry_run_summary=None)


def render_session_status_with_dry_run(
    session: RepairSession, *, dry_run_summary: dict[str, Any] | None
) -> str:
    """Render current session state for human CLI output with dry-run details."""
    dry_run_line = "Executor dry-run: none"
    dry_run_source_line = "Executor dry-run source: none"
    dry_run_decision_line = "Executor dry-run decision: none"
    dry_run_diagnostic_line = "Executor dry-run diagnostic: none"
    dry_run_action_line = "Executor dry-run action: none"
    if dry_run_summary:
        verdict = str(dry_run_summary.get("verdict") or "unknown")
        reason = str(dry_run_summary.get("verdict_reason") or "").strip()
        source = str(dry_run_summary.get("summary_source") or "").strip() or "unknown"
        decision = str(dry_run_summary.get("operator_decision") or "").strip()
        diagnostic = str(dry_run_summary.get("operator_summary") or "").strip()
        actions = normalized_dry_run_actions(dry_run_summary.get("recommended_actions"))
        dry_run_line = (
            f"Executor dry-run: {verdict} ({reason})"
            if reason
            else f"Executor dry-run: {verdict}"
        )
        dry_run_source_line = f"Executor dry-run source: {source}"
        if decision:
            dry_run_decision_line = f"Executor dry-run decision: {decision}"
        if diagnostic:
            dry_run_diagnostic_line = f"Executor dry-run diagnostic: {diagnostic}"
        if actions:
            dry_run_action_line = f"Executor dry-run action: {actions[0]['summary']}"
    return "\n".join(
        [
            f"qa-z repair-session: {session.state}",
            f"Session: {session.session_dir}",
            f"Baseline run: {session.baseline_run_dir}",
            f"Handoff: {session.handoff_dir}",
            f"Candidate run: {session.candidate_run_dir or 'none'}",
            f"Verify: {session.verify_dir or 'none'}",
            f"Outcome: {session.outcome_path or 'none'}",
            f"Executor result: {session.executor_result_status or 'none'}",
            dry_run_line,
            dry_run_source_line,
            dry_run_decision_line,
            dry_run_diagnostic_line,
            dry_run_action_line,
        ]
    )


def render_session_start_stdout(session: RepairSession) -> str:
    """Render session creation output."""
    return "\n".join(
        [
            f"qa-z repair-session start: {session.state}",
            f"Session: {session.session_dir}",
            f"Baseline run: {session.baseline_run_dir}",
            f"Handoff: {session.handoff_dir}",
            f"Executor guide: {session.executor_guide_path}",
        ]
    )


def render_session_verify_stdout(
    session: RepairSession, summary: dict[str, Any]
) -> str:
    """Render session verification output."""
    return "\n".join(
        [
            f"qa-z repair-session verify: {summary['verdict']}",
            f"Session: {session.session_dir}",
            f"Candidate run: {session.candidate_run_dir or 'none'}",
            f"Verify: {session.verify_dir or 'none'}",
            f"Outcome: {session.outcome_path or 'none'}",
        ]
    )
