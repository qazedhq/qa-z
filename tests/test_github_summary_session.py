"""Behavior tests for GitHub summary repair-session surfaces."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_z.cli import main
from tests.github_summary_test_support import (
    make_executor_history_attempt,
    write_config,
    write_contract,
    write_executor_result_history,
    write_session_outcome_for_run,
    write_summary,
)


def test_github_summary_includes_repair_session_outcome_when_present(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path,
        session_id="session-one",
        candidate_run="candidate",
        executor_dry_run_verdict="blocked",
        executor_dry_run_reason="completed_attempt_not_verification_clean",
        executor_dry_run_source="materialized",
        executor_dry_run_attempt_count=2,
        executor_dry_run_history_signals=["repeated_partial_attempts"],
    )

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/candidate",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Repair Session Outcome" in output
    assert "- Verdict: improved" in output
    assert "- Resolved blockers: 2" in output
    assert "- Remaining blockers: 1" in output
    assert "- Regressions: 0" in output
    assert "- Recommendation: safe_to_review" in output
    assert "- Executor dry-run: blocked" in output
    assert "- Dry-run reason: completed_attempt_not_verification_clean" in output
    assert "- Dry-run source: materialized" in output
    assert "- Executor attempts: 2" in output
    assert "- Executor history signals: repeated_partial_attempts" in output
    assert "- Session: `.qa-z/sessions/session-one/session.json`" in output


def test_github_summary_synthesizes_dry_run_from_history_when_summary_lacks_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path,
        session_id="session-one",
        candidate_run="candidate",
    )
    write_executor_result_history(
        tmp_path,
        session_id="session-one",
        attempts=[
            make_executor_history_attempt("attempt-1"),
            make_executor_history_attempt("attempt-2"),
        ],
    )

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/candidate",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Repair Session Outcome" in output
    assert "- Executor dry-run: attention_required" in output
    assert "- Dry-run reason: manual_retry_review_required" in output
    assert "- Dry-run source: history_fallback" in output
    assert "- Executor attempts: 2" in output
    assert "- Executor history signals: repeated_partial_attempts" in output


def test_github_summary_can_render_explicit_session_outcome(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path, session_id="session-one", candidate_run="candidate"
    )

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/candidate",
            "--from-session",
            ".qa-z/sessions/session-one",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Repair Session Outcome" in output
    assert "- Outcome: `.qa-z/sessions/session-one/outcome.md`" in output


def test_github_summary_explicit_session_uses_verify_fallback_when_summary_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path,
        session_id="session-one",
        candidate_run="candidate",
        verdict="mixed",
    )
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    (session_dir / "summary.json").unlink()
    write_executor_result_history(
        tmp_path,
        session_id="session-one",
        attempts=[
            make_executor_history_attempt(
                "attempt-1",
                changed_files_count=2,
                provenance_status="failed",
                provenance_reason="scope_validation_failed",
            )
        ],
    )

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/candidate",
            "--from-session",
            ".qa-z/sessions/session-one",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Repair Session Outcome" in output
    assert "- Verdict: mixed" in output
    assert "- Recommendation: review_required" in output
    assert "- Executor dry-run: blocked" in output
    assert "- Dry-run reason: scope_validation_failed" in output
    assert "- Dry-run source: history_fallback" in output
    assert "- Executor attempts: 1" in output
    assert "- Executor history signals: scope_validation_failed" in output
    assert "Verification artifacts could not be read." not in output


def test_github_summary_explicit_session_prefers_candidate_run_when_from_run_omitted(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path, session_id="session-one", candidate_run="candidate"
    )
    write_summary(tmp_path, "latest-other")

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-session",
            ".qa-z/sessions/session-one",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "- Fast summary: `.qa-z/runs/candidate/fast/summary.json`" in output
    assert "- Outcome: `.qa-z/sessions/session-one/outcome.md`" in output
    assert "- Session: `.qa-z/sessions/session-one/session.json`" in output


def test_github_summary_explicit_run_still_overrides_session_candidate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "candidate")
    write_session_outcome_for_run(
        tmp_path, session_id="session-one", candidate_run="candidate"
    )
    write_summary(tmp_path, "manual-run")

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/manual-run",
            "--from-session",
            ".qa-z/sessions/session-one",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "- Fast summary: `.qa-z/runs/manual-run/fast/summary.json`" in output
    assert "- Session: `.qa-z/sessions/session-one/session.json`" in output
