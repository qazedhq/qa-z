"""Behavior tests for verification publish summary surfaces."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_z.reporters.verification_publish import (
    build_verification_publish_summary,
    recommendation_for_verdict,
    render_publish_summary_markdown,
)
from tests.verification_publish_test_support import write_verify_artifacts


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
