"""Behavior tests for repair-session render helpers."""

from __future__ import annotations

from qa_z.repair_session import RepairSession
from qa_z.repair_session_render import (
    render_session_start_stdout,
    render_session_status_with_dry_run,
    render_session_verify_stdout,
)


def _session() -> RepairSession:
    return RepairSession(
        session_id="session-one",
        session_dir=".qa-z/sessions/session-one",
        baseline_run_dir=".qa-z/runs/baseline",
        handoff_dir=".qa-z/sessions/session-one/handoff",
        executor_guide_path=".qa-z/sessions/session-one/executor-guide.md",
        state="waiting_for_external_repair",
        created_at="2026-04-22T00:00:00Z",
        updated_at="2026-04-22T00:00:00Z",
        baseline_fast_summary_path=".qa-z/runs/baseline/fast/summary.json",
    )


def test_render_session_start_stdout_reports_core_paths() -> None:
    output = render_session_start_stdout(_session())

    assert "qa-z repair-session start: waiting_for_external_repair" in output
    assert "Session: .qa-z/sessions/session-one" in output
    assert "Executor guide: .qa-z/sessions/session-one/executor-guide.md" in output


def test_render_session_status_with_dry_run_includes_decision_and_action() -> None:
    output = render_session_status_with_dry_run(
        _session(),
        dry_run_summary={
            "verdict": "blocked",
            "verdict_reason": "completed_attempt_not_verification_clean",
            "summary_source": "materialized",
            "operator_decision": "manual_review",
            "operator_summary": "Verification is still blocking acceptance.",
            "recommended_actions": [
                {
                    "id": "review-summary",
                    "summary": "Review verify/summary.json before retrying.",
                }
            ],
        },
    )

    assert (
        "Executor dry-run: blocked (completed_attempt_not_verification_clean)" in output
    )
    assert "Executor dry-run source: materialized" in output
    assert "Executor dry-run decision: manual_review" in output
    assert (
        "Executor dry-run diagnostic: Verification is still blocking acceptance."
        in output
    )
    assert (
        "Executor dry-run action: Review verify/summary.json before retrying." in output
    )


def test_render_session_verify_stdout_reports_verdict_and_paths() -> None:
    output = render_session_verify_stdout(
        _session(),
        {
            "verdict": "improved",
        },
    )

    assert "qa-z repair-session verify: improved" in output
    assert "Session: .qa-z/sessions/session-one" in output
    assert "Verify: none" in output
    assert "Outcome: none" in output
