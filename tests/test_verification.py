"""Tests for post-repair verification comparisons."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.verification import (
    write_verification_artifacts,
    compare_verification_runs,
)
from tests.verification_test_support import check_result, verification_run


def test_write_verification_artifacts_emits_summary_compare_and_report(
    tmp_path: Path,
) -> None:
    comparison = compare_verification_runs(
        verification_run(
            "baseline",
            fast_checks=[check_result("py_test", "failed", kind="test", exit_code=1)],
        ),
        verification_run(
            "candidate",
            fast_checks=[check_result("py_test", "passed", kind="test", exit_code=0)],
        ),
    )

    paths = write_verification_artifacts(comparison, tmp_path / "verify")

    assert paths.summary_path == tmp_path / "verify" / "summary.json"
    assert paths.compare_path == tmp_path / "verify" / "compare.json"
    assert paths.report_path == tmp_path / "verify" / "report.md"
    assert json.loads(paths.summary_path.read_text(encoding="utf-8")) == {
        "kind": "qa_z.verify_summary",
        "schema_version": 1,
        "repair_improved": True,
        "verdict": "improved",
        "blocking_before": 1,
        "blocking_after": 0,
        "resolved_count": 1,
        "remaining_issue_count": 0,
        "new_issue_count": 0,
        "regression_count": 0,
        "not_comparable_count": 0,
    }
    assert (
        json.loads(paths.compare_path.read_text(encoding="utf-8"))["kind"]
        == "qa_z.verify_compare"
    )
    report = paths.report_path.read_text(encoding="utf-8")
    assert "# QA-Z Repair Verification" in report
    assert "Final verdict: `improved`" in report


def test_verification_summary_reports_remaining_issue_count_for_unchanged_case(
    tmp_path: Path,
) -> None:
    comparison = compare_verification_runs(
        verification_run(
            "baseline",
            fast_checks=[
                check_result("docs_schema", "failed", kind="lint", exit_code=1)
            ],
        ),
        verification_run(
            "candidate",
            fast_checks=[
                check_result("docs_schema", "failed", kind="lint", exit_code=1)
            ],
        ),
    )

    paths = write_verification_artifacts(comparison, tmp_path / "verify")
    summary = json.loads(paths.summary_path.read_text(encoding="utf-8"))

    assert comparison.verdict == "unchanged"
    assert summary["remaining_issue_count"] == 1
    assert summary["repair_improved"] is False
