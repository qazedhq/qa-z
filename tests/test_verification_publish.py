"""Tests for concise verification/session publishing summaries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.reporters.verification_publish import (
    build_verification_publish_summary,
    load_session_publish_summary,
    recommendation_for_verdict,
    render_publish_summary_markdown,
)


def write_verify_artifacts(
    root: Path,
    verify_dir: Path,
    *,
    verdict: str,
    baseline_run_id: str = "baseline",
    candidate_run_id: str = "candidate",
    blocking_after: int,
    resolved_count: int,
    regression_count: int,
    new_issue_count: int | None = None,
) -> None:
    """Write compact verification artifacts for publishing tests."""
    verify_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "kind": "qa_z.verify_summary",
        "schema_version": 1,
        "repair_improved": verdict == "improved",
        "verdict": verdict,
        "blocking_before": 3,
        "blocking_after": blocking_after,
        "resolved_count": resolved_count,
        "new_issue_count": (
            regression_count if new_issue_count is None else new_issue_count
        ),
        "regression_count": regression_count,
        "not_comparable_count": 0,
    }
    compare = {
        "kind": "qa_z.verify_compare",
        "schema_version": 1,
        "baseline_run_id": baseline_run_id,
        "candidate_run_id": candidate_run_id,
        "baseline": {"run_dir": f".qa-z/runs/{baseline_run_id}"},
        "candidate": {"run_dir": f".qa-z/runs/{candidate_run_id}"},
        "verdict": verdict,
        "summary": {
            "blocking_before": 3,
            "blocking_after": blocking_after,
            "resolved_count": resolved_count,
            "new_issue_count": (
                regression_count if new_issue_count is None else new_issue_count
            ),
            "regression_count": regression_count,
        },
    }
    (verify_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (verify_dir / "compare.json").write_text(
        json.dumps(compare, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (verify_dir / "report.md").write_text(
        "# QA-Z Repair Verification\n", encoding="utf-8"
    )


def write_executor_result_history(
    root: Path,
    session_id: str,
    *,
    attempts: list[dict[str, object]],
) -> None:
    """Write a compact session-local executor-result history artifact."""
    path = (
        root / ".qa-z" / "sessions" / session_id / "executor_results" / "history.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "kind": "qa_z.executor_result_history",
                "schema_version": 1,
                "session_id": session_id,
                "updated_at": "2026-04-16T00:00:02Z",
                "attempt_count": len(attempts),
                "latest_attempt_id": attempts[-1]["attempt_id"] if attempts else None,
                "attempts": attempts,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    ("verdict", "recommendation"),
    [
        ("improved", "safe_to_review"),
        ("mixed", "review_required"),
        ("regressed", "do_not_merge"),
        ("verification_failed", "rerun_required"),
        ("unchanged", "continue_repair"),
    ],
)
def test_recommendation_for_verdict(verdict: str, recommendation: str) -> None:
    assert recommendation_for_verdict(verdict) == recommendation


def test_verification_publish_summary_renders_improved_case(tmp_path: Path) -> None:
    verify_dir = tmp_path / ".qa-z" / "runs" / "candidate" / "verify"
    write_verify_artifacts(
        tmp_path,
        verify_dir,
        verdict="improved",
        blocking_after=1,
        resolved_count=2,
        regression_count=0,
    )

    summary = build_verification_publish_summary(root=tmp_path, verify_dir=verify_dir)
    markdown = render_publish_summary_markdown(summary)

    assert summary.baseline_run_id == "baseline"
    assert summary.candidate_run_id == "candidate"
    assert summary.final_verdict == "improved"
    assert summary.resolved_count == 2
    assert summary.remaining_blocker_count == 1
    assert summary.regression_count == 0
    assert summary.recommendation == "safe_to_review"
    assert "2 resolved, 1 remaining, 0 regressions." in summary.headline
    assert "## Repair Verification Outcome" in markdown
    assert "- Verdict: improved" in markdown
    assert "- Recommendation: safe_to_review" in markdown
    assert "- Verify summary: `.qa-z/runs/candidate/verify/summary.json`" in markdown
    assert "### Action Needed" not in markdown


@pytest.mark.parametrize(
    ("verdict", "resolved_count", "blocking_after", "regression_count", "expected"),
    [
        ("mixed", 1, 2, 1, "review_required"),
        ("regressed", 0, 2, 1, "do_not_merge"),
    ],
)
def test_verification_publish_summary_handles_risky_outcomes(
    tmp_path: Path,
    verdict: str,
    resolved_count: int,
    blocking_after: int,
    regression_count: int,
    expected: str,
) -> None:
    verify_dir = tmp_path / ".qa-z" / "runs" / "candidate" / "verify"
    write_verify_artifacts(
        tmp_path,
        verify_dir,
        verdict=verdict,
        blocking_after=blocking_after,
        resolved_count=resolved_count,
        regression_count=regression_count,
    )

    summary = build_verification_publish_summary(root=tmp_path, verify_dir=verify_dir)
    markdown = render_publish_summary_markdown(summary)

    assert summary.recommendation == expected
    assert f"- Recommendation: {expected}" in markdown
    assert "### Action Needed" in markdown


def test_verification_publish_summary_reports_missing_artifacts(
    tmp_path: Path,
) -> None:
    verify_dir = tmp_path / ".qa-z" / "runs" / "candidate" / "verify"

    summary = build_verification_publish_summary(root=tmp_path, verify_dir=verify_dir)
    markdown = render_publish_summary_markdown(summary)

    assert summary.final_verdict == "verification_failed"
    assert summary.recommendation == "rerun_required"
    assert summary.resolved_count == 0
    assert summary.remaining_blocker_count == 0
    assert "Verification artifacts could not be read." in summary.headline
    assert "- Recommendation: rerun_required" in markdown
    assert "Rerun verification before merge." in markdown


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
    (session_dir / "summary.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.repair_session_summary",
                "schema_version": 1,
                "session_id": "session-one",
                "state": "completed",
                "baseline_run_dir": ".qa-z/runs/baseline",
                "candidate_run_dir": ".qa-z/runs/candidate",
                "verify_dir": ".qa-z/sessions/session-one/verify",
                "outcome_path": ".qa-z/sessions/session-one/outcome.md",
                "verdict": "mixed",
                "blocking_before": 3,
                "blocking_after": 2,
                "resolved_count": 1,
                "remaining_issue_count": 2,
                "new_issue_count": 1,
                "regression_count": 1,
                "not_comparable_count": 0,
                "next_recommendation": "inspect regressions",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.repair_session",
                "schema_version": 1,
                "session_id": "session-one",
                "session_dir": ".qa-z/sessions/session-one",
                "state": "completed",
                "baseline_run_dir": ".qa-z/runs/baseline",
                "candidate_run_dir": ".qa-z/runs/candidate",
                "verify_dir": ".qa-z/sessions/session-one/verify",
                "verify_artifacts": {
                    "summary_json": ".qa-z/sessions/session-one/verify/summary.json",
                    "compare_json": ".qa-z/sessions/session-one/verify/compare.json",
                    "report_markdown": ".qa-z/sessions/session-one/verify/report.md",
                },
                "outcome_path": ".qa-z/sessions/session-one/outcome.md",
                "summary_path": ".qa-z/sessions/session-one/summary.json",
                "handoff_dir": ".qa-z/sessions/session-one/handoff",
                "handoff_artifacts": {
                    "handoff_json": ".qa-z/sessions/session-one/handoff/handoff.json"
                },
                "executor_guide_path": ".qa-z/sessions/session-one/executor_guide.md",
                "created_at": "2026-04-14T00:00:00Z",
                "updated_at": "2026-04-14T00:00:01Z",
                "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
                "provenance": {},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

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
            {
                "attempt_id": "attempt-1",
                "recorded_at": "2026-04-16T00:00:01Z",
                "bridge_id": "bridge-session",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-1.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "recorded_at": "2026-04-16T00:00:02Z",
                "bridge_id": "bridge-session",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-2.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
        ],
    )
    (session_dir / "summary.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.repair_session_summary",
                "schema_version": 1,
                "session_id": "session-one",
                "state": "completed",
                "baseline_run_dir": ".qa-z/runs/baseline",
                "candidate_run_dir": ".qa-z/runs/candidate",
                "verify_dir": ".qa-z/sessions/session-one/verify",
                "outcome_path": ".qa-z/sessions/session-one/outcome.md",
                "verdict": "unchanged",
                "blocking_before": 2,
                "blocking_after": 2,
                "resolved_count": 0,
                "remaining_issue_count": 2,
                "new_issue_count": 0,
                "regression_count": 0,
                "not_comparable_count": 0,
                "next_recommendation": "continue repair",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.repair_session",
                "schema_version": 1,
                "session_id": "session-one",
                "session_dir": ".qa-z/sessions/session-one",
                "state": "completed",
                "baseline_run_dir": ".qa-z/runs/baseline",
                "candidate_run_dir": ".qa-z/runs/candidate",
                "verify_dir": ".qa-z/sessions/session-one/verify",
                "verify_artifacts": {
                    "summary_json": ".qa-z/sessions/session-one/verify/summary.json",
                    "compare_json": ".qa-z/sessions/session-one/verify/compare.json",
                    "report_markdown": ".qa-z/sessions/session-one/verify/report.md",
                },
                "outcome_path": ".qa-z/sessions/session-one/outcome.md",
                "summary_path": ".qa-z/sessions/session-one/summary.json",
                "handoff_dir": ".qa-z/sessions/session-one/handoff",
                "handoff_artifacts": {
                    "handoff_json": ".qa-z/sessions/session-one/handoff/handoff.json"
                },
                "executor_guide_path": ".qa-z/sessions/session-one/executor_guide.md",
                "created_at": "2026-04-14T00:00:00Z",
                "updated_at": "2026-04-14T00:00:01Z",
                "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
                "provenance": {},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

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
    assert (
        "- Dry-run recommended actions: Review unresolved repair targets across "
        "repeated partial attempts before retrying." in markdown
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
            {
                "attempt_id": "attempt-1",
                "recorded_at": "2026-04-16T00:00:01Z",
                "bridge_id": "bridge-session",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 2,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-1.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "failed",
                "provenance_reason": "scope_validation_failed",
            }
        ],
    )
    (session_dir / "session.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.repair_session",
                "schema_version": 1,
                "session_id": "session-one",
                "session_dir": ".qa-z/sessions/session-one",
                "state": "completed",
                "baseline_run_dir": ".qa-z/runs/baseline",
                "candidate_run_dir": ".qa-z/runs/candidate",
                "verify_dir": ".qa-z/sessions/session-one/verify",
                "verify_artifacts": {
                    "summary_json": ".qa-z/sessions/session-one/verify/summary.json",
                    "compare_json": ".qa-z/sessions/session-one/verify/compare.json",
                    "report_markdown": ".qa-z/sessions/session-one/verify/report.md",
                },
                "outcome_path": ".qa-z/sessions/session-one/outcome.md",
                "summary_path": ".qa-z/sessions/session-one/summary.json",
                "handoff_dir": ".qa-z/sessions/session-one/handoff",
                "handoff_artifacts": {
                    "handoff_json": ".qa-z/sessions/session-one/handoff/handoff.json"
                },
                "executor_guide_path": ".qa-z/sessions/session-one/executor_guide.md",
                "created_at": "2026-04-14T00:00:00Z",
                "updated_at": "2026-04-14T00:00:01Z",
                "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
                "provenance": {},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

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
    assert (
        "- Dry-run recommended actions: Inspect changed files against the bridge "
        "handoff scope before another attempt." in markdown
    )
