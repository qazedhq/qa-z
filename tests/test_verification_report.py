"""Behavior tests for verification report helpers."""

from __future__ import annotations

from qa_z.verification import compare_verification_runs
from qa_z.verification_report import render_verification_report_impl
from tests.verification_test_support import check_result, finding, verification_run


def test_verification_report_mentions_fast_and_deep_sections() -> None:
    baseline = verification_run(
        "baseline",
        fast_checks=[check_result("py_test", "failed", kind="test", exit_code=1)],
        deep_checks=[
            check_result(
                "sg_scan",
                "failed",
                kind="static-analysis",
                findings=[finding("rule.one", "src/app.py", 10, "Blocker")],
                blocking_findings_count=1,
            )
        ],
    )
    candidate = verification_run(
        "candidate",
        fast_checks=[check_result("py_test", "passed", kind="test", exit_code=0)],
        deep_checks=[
            check_result(
                "sg_scan",
                "passed",
                kind="static-analysis",
                findings=[],
                blocking_findings_count=0,
            )
        ],
    )

    report = render_verification_report_impl(
        compare_verification_runs(baseline, candidate)
    )

    assert "## Fast Checks" in report
    assert "## Deep Findings" in report
    assert "### Resolved" in report
