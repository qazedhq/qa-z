"""Behavior tests for session-backed verification publish summaries."""

from __future__ import annotations

from pathlib import Path

from qa_z.reporters.verification_publish import (
    load_session_publish_summary,
    render_publish_summary_markdown,
)
from tests.verification_publish_test_support import (
    executor_attempt,
    write_executor_result_history,
    write_session_manifest,
    write_session_summary,
    write_verify_artifacts,
)


def test_session_publish_summary_uses_session_artifacts(tmp_path: Path) -> None:
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    verify_dir = session_dir / "verify"
    write_verify_artifacts(
        tmp_path,
        verify_dir,
        verdict="mixed",
        blocking_after=2,
        resolved_count=1,
        regression_count=1,
    )
    write_session_summary(
        tmp_path,
        "session-one",
        verdict="mixed",
        blocking_before=3,
        blocking_after=2,
        resolved_count=1,
        remaining_issue_count=2,
        new_issue_count=1,
        regression_count=1,
        next_recommendation="inspect regressions",
    )
    write_session_manifest(tmp_path, "session-one")

    summary = load_session_publish_summary(root=tmp_path, session="session-one")
    markdown = render_publish_summary_markdown(summary)

    assert summary.session_id == "session-one"
    assert summary.verification.final_verdict == "mixed"
    assert summary.verification.recommendation == "review_required"
    assert "## Repair Session Outcome" in markdown
    assert "- Session: `.qa-z/sessions/session-one/session.json`" in markdown
    assert "- Outcome: `.qa-z/sessions/session-one/outcome.md`" in markdown
    assert "- Handoff: `.qa-z/sessions/session-one/handoff/handoff.json`" in markdown


def test_session_publish_summary_synthesizes_dry_run_from_history(
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    verify_dir = session_dir / "verify"
    write_verify_artifacts(
        tmp_path,
        verify_dir,
        verdict="unchanged",
        blocking_after=2,
        resolved_count=0,
        regression_count=0,
        new_issue_count=0,
    )
    write_executor_result_history(
        tmp_path,
        "session-one",
        attempts=[
            executor_attempt(
                "session-one",
                "attempt-1",
                recorded_at="2026-04-16T00:00:01Z",
                bridge_id="bridge-session",
            ),
            executor_attempt(
                "session-one",
                "attempt-2",
                recorded_at="2026-04-16T00:00:02Z",
                bridge_id="bridge-session",
            ),
        ],
    )
    write_session_summary(
        tmp_path,
        "session-one",
        verdict="unchanged",
        blocking_before=2,
        blocking_after=2,
        resolved_count=0,
        remaining_issue_count=2,
        new_issue_count=0,
        regression_count=0,
        next_recommendation="continue repair",
    )
    write_session_manifest(tmp_path, "session-one")

    summary = load_session_publish_summary(root=tmp_path, session="session-one")
    markdown = render_publish_summary_markdown(summary)

    assert summary.executor_dry_run_verdict == "attention_required"
    assert summary.executor_dry_run_reason == "manual_retry_review_required"
    assert summary.executor_dry_run_source == "history_fallback"
    assert summary.executor_dry_run_attempt_count == 2
    assert summary.executor_dry_run_history_signals == ["repeated_partial_attempts"]
    assert summary.executor_dry_run_operator_decision == "inspect_partial_attempts"
    assert summary.executor_dry_run_operator_summary == (
        "Repeated partial executor attempts need manual review before another retry."
    )
    assert summary.executor_dry_run_recommended_actions == [
        {
            "id": "inspect_partial_attempts",
            "summary": (
                "Review unresolved repair targets across repeated partial attempts "
                "before retrying."
            ),
        }
    ]
    assert "- Executor dry-run: attention_required" in markdown
    assert "- Dry-run reason: manual_retry_review_required" in markdown
    assert "- Dry-run source: history_fallback" in markdown
    assert "- Executor attempts: 2" in markdown
    assert "- Executor history signals: repeated_partial_attempts" in markdown
    assert "- Dry-run operator decision: inspect_partial_attempts" in markdown
    assert (
        "- Dry-run operator summary: Repeated partial executor attempts need manual "
        "review before another retry." in markdown
    )
    assert "- Dry-run recommended actions:" in markdown
    assert (
        "- Action `inspect_partial_attempts`: Review unresolved repair targets "
        "across repeated partial attempts before retrying." in markdown
    )


def test_session_publish_summary_falls_back_to_verify_artifacts_when_summary_missing(
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    verify_dir = session_dir / "verify"
    write_verify_artifacts(
        tmp_path,
        verify_dir,
        verdict="mixed",
        blocking_after=2,
        resolved_count=1,
        regression_count=1,
    )
    write_executor_result_history(
        tmp_path,
        "session-one",
        attempts=[
            executor_attempt(
                "session-one",
                "attempt-1",
                recorded_at="2026-04-16T00:00:01Z",
                bridge_id="bridge-session",
                changed_files_count=2,
                provenance_status="failed",
                provenance_reason="scope_validation_failed",
            )
        ],
    )
    write_session_manifest(tmp_path, "session-one")

    summary = load_session_publish_summary(root=tmp_path, session="session-one")
    markdown = render_publish_summary_markdown(summary)

    assert summary.verification.final_verdict == "mixed"
    assert summary.verification.recommendation == "review_required"
    assert summary.verification.resolved_count == 1
    assert summary.verification.remaining_blocker_count == 2
    assert summary.verification.regression_count == 1
    assert summary.executor_dry_run_verdict == "blocked"
    assert summary.executor_dry_run_reason == "scope_validation_failed"
    assert summary.executor_dry_run_source == "history_fallback"
    assert summary.executor_dry_run_attempt_count == 1
    assert summary.executor_dry_run_history_signals == ["scope_validation_failed"]
    assert summary.executor_dry_run_operator_decision == "inspect_scope_drift"
    assert summary.executor_dry_run_operator_summary == (
        "Executor history is blocked by scope validation; inspect handoff scope "
        "before another attempt."
    )
    assert summary.executor_dry_run_recommended_actions == [
        {
            "id": "inspect_scope_drift",
            "summary": (
                "Inspect changed files against the bridge handoff scope before "
                "another attempt."
            ),
        }
    ]
    assert "- Verdict: mixed" in markdown
    assert "- Recommendation: review_required" in markdown
    assert "- Executor dry-run: blocked" in markdown
    assert "- Dry-run reason: scope_validation_failed" in markdown
    assert "- Dry-run source: history_fallback" in markdown
    assert "- Executor attempts: 1" in markdown
    assert "- Executor history signals: scope_validation_failed" in markdown
    assert "- Dry-run operator decision: inspect_scope_drift" in markdown
    assert "- Dry-run recommended actions:" in markdown
    assert (
        "- Action `inspect_scope_drift`: Inspect changed files against the bridge "
        "handoff scope before another attempt." in markdown
    )


def test_session_publish_summary_preserves_blocked_mixed_history_action_lines(
    tmp_path: Path,
) -> None:
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-mixed"
    verify_dir = session_dir / "verify"
    write_verify_artifacts(
        tmp_path,
        verify_dir,
        verdict="mixed",
        blocking_after=1,
        resolved_count=1,
        regression_count=0,
        new_issue_count=0,
    )
    write_executor_result_history(
        tmp_path,
        "session-mixed",
        attempts=[
            executor_attempt(
                "session-mixed",
                "attempt-1",
                recorded_at="2026-04-18T01:00:00Z",
                bridge_id="bridge-partial",
            ),
            executor_attempt(
                "session-mixed",
                "attempt-2",
                recorded_at="2026-04-18T01:03:00Z",
                bridge_id="bridge-partial",
            ),
            executor_attempt(
                "session-mixed",
                "attempt-3",
                recorded_at="2026-04-18T01:05:00Z",
                bridge_id="bridge-partial",
                result_status="completed",
                ingest_status="accepted_with_warning",
                verification_hint="rerun",
                verification_verdict="mixed",
                warning_ids=["completed_validation_failed"],
                backlog_categories=["partial_completion_gap", "workflow_gap"],
            ),
        ],
    )
    write_session_summary(
        tmp_path,
        "session-mixed",
        verdict="mixed",
        blocking_before=2,
        blocking_after=1,
        resolved_count=1,
        remaining_issue_count=1,
        new_issue_count=0,
        regression_count=0,
        next_recommendation="inspect regressions",
    )
    write_session_manifest(tmp_path, "session-mixed")

    summary = load_session_publish_summary(root=tmp_path, session="session-mixed")
    markdown = render_publish_summary_markdown(summary)

    assert summary.executor_dry_run_verdict == "blocked"
    assert summary.executor_dry_run_reason == "completed_attempt_not_verification_clean"
    assert summary.executor_dry_run_source == "history_fallback"
    assert summary.executor_dry_run_attempt_count == 3
    assert summary.executor_dry_run_history_signals == [
        "repeated_partial_attempts",
        "completed_verify_blocked",
        "validation_conflict",
    ]
    assert summary.executor_dry_run_operator_decision == "resolve_verification_blockers"
    assert summary.executor_dry_run_operator_summary == (
        "A completed executor attempt is still blocked by verification evidence; "
        "validation conflicts and retry pressure still need review before another "
        "retry."
    )
    assert summary.executor_dry_run_recommended_actions == [
        {
            "id": "resolve_verification_blockers",
            "summary": (
                "Review verify/summary.json and repair remaining or regressed "
                "blockers before accepting completion."
            ),
        },
        {
            "id": "review_validation_conflict",
            "summary": (
                "Compare executor validation claims with deterministic verification "
                "artifacts before retrying."
            ),
        },
        {
            "id": "inspect_partial_attempts",
            "summary": (
                "Review unresolved repair targets across repeated partial attempts "
                "before retrying."
            ),
        },
    ]
    assert "- Dry-run recommended actions:" in markdown
    assert (
        "- Action `resolve_verification_blockers`: Review verify/summary.json and "
        "repair remaining or regressed blockers before accepting completion."
        in markdown
    )
    assert (
        "- Action `review_validation_conflict`: Compare executor validation claims "
        "with deterministic verification artifacts before retrying." in markdown
    )
    assert (
        "- Action `inspect_partial_attempts`: Review unresolved repair targets "
        "across repeated partial attempts before retrying." in markdown
    )
