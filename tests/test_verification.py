"""Tests for post-repair verification comparisons."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.runners.models import CheckResult, RunSummary
from qa_z.verification import (
    VerificationRun,
    compare_verification_runs,
    write_verification_artifacts,
)


def check_result(
    check_id: str,
    status: str,
    *,
    kind: str = "test",
    exit_code: int | None = None,
    findings: list[dict[str, object]] | None = None,
    grouped_findings: list[dict[str, object]] | None = None,
    blocking_findings_count: int | None = None,
    policy: dict[str, object] | None = None,
) -> CheckResult:
    """Build a compact check result for verification tests."""
    return CheckResult(
        id=check_id,
        tool=check_id,
        command=[check_id],
        kind=kind,
        status=status,
        exit_code=exit_code,
        duration_ms=1,
        findings_count=(
            len(findings or grouped_findings or [])
            if findings is not None or grouped_findings is not None
            else None
        ),
        blocking_findings_count=blocking_findings_count,
        filtered_findings_count=0 if findings is not None else None,
        findings=list(findings or []),
        grouped_findings=list(grouped_findings or []),
        policy=dict(policy or {}),
    )


def run_summary(mode: str, checks: list[CheckResult], *, run_id: str) -> RunSummary:
    """Build a minimal fast or deep summary."""
    failed = any(check.status in {"failed", "error"} for check in checks)
    return RunSummary(
        mode=mode,
        contract_path="qa/contracts/example.md",
        project_root=str(Path("/repo")),
        status="failed" if failed else "passed",
        started_at="2026-04-14T00:00:00Z",
        finished_at="2026-04-14T00:00:01Z",
        checks=checks,
        artifact_dir=f".qa-z/runs/{run_id}/{mode}",
        schema_version=2,
    )


def verification_run(
    run_id: str,
    *,
    fast_checks: list[CheckResult],
    deep_checks: list[CheckResult] | None = None,
) -> VerificationRun:
    """Build verification evidence for one run."""
    return VerificationRun(
        run_id=run_id,
        run_dir=f".qa-z/runs/{run_id}",
        fast_summary=run_summary("fast", fast_checks, run_id=run_id),
        deep_summary=(
            run_summary("deep", deep_checks, run_id=run_id)
            if deep_checks is not None
            else None
        ),
    )


def ids(items: list[dict[str, object]]) -> list[str]:
    """Return item ids from serialized delta records."""
    return [str(item["id"]) for item in items]


def finding(rule_id: str, path: str, line: int, message: str) -> dict[str, object]:
    """Build a normalized deep finding."""
    return {
        "rule_id": rule_id,
        "severity": "ERROR",
        "path": path,
        "line": line,
        "message": message,
    }


def test_fast_check_comparison_classifies_resolved_still_and_regressed() -> None:
    baseline = verification_run(
        "baseline",
        fast_checks=[
            check_result("py_type", "failed", kind="typecheck", exit_code=1),
            check_result("py_test", "failed", kind="test", exit_code=1),
            check_result("ts_lint", "passed", kind="lint", exit_code=0),
            check_result("docs_spell", "skipped", kind="lint"),
        ],
    )
    candidate = verification_run(
        "candidate",
        fast_checks=[
            check_result("py_type", "passed", kind="typecheck", exit_code=0),
            check_result("py_test", "failed", kind="test", exit_code=1),
            check_result("ts_lint", "failed", kind="lint", exit_code=1),
            check_result("docs_spell", "skipped", kind="lint"),
        ],
    )

    comparison = compare_verification_runs(baseline, candidate).to_dict()

    assert comparison["verdict"] == "mixed"
    assert ids(comparison["fast_checks"]["resolved"]) == ["py_type"]
    assert ids(comparison["fast_checks"]["still_failing"]) == ["py_test"]
    assert ids(comparison["fast_checks"]["regressed"]) == ["ts_lint"]
    assert ids(comparison["fast_checks"]["skipped_or_not_comparable"]) == ["docs_spell"]


def test_deep_finding_comparison_uses_relaxed_identity_for_message_changes() -> None:
    baseline = verification_run(
        "baseline",
        fast_checks=[],
        deep_checks=[
            check_result(
                "sg_scan",
                "failed",
                kind="static-analysis",
                findings=[
                    finding(
                        "python.lang.security.audit.eval",
                        "src/app.py",
                        42,
                        "Avoid use of eval.",
                    )
                ],
                blocking_findings_count=1,
                policy={"fail_on_severity": ["ERROR"]},
            )
        ],
    )
    candidate = verification_run(
        "candidate",
        fast_checks=[],
        deep_checks=[
            check_result(
                "sg_scan",
                "failed",
                kind="static-analysis",
                findings=[
                    finding(
                        "python.lang.security.audit.eval",
                        "src\\app.py",
                        42,
                        "Avoid use of eval",
                    )
                ],
                blocking_findings_count=1,
                policy={"fail_on_severity": ["ERROR"]},
            )
        ],
    )

    comparison = compare_verification_runs(baseline, candidate).to_dict()

    assert comparison["verdict"] == "unchanged"
    assert ids(comparison["deep_findings"]["still_failing"]) == [
        "sg_scan:python.lang.security.audit.eval:src/app.py:42"
    ]
    assert comparison["deep_findings"]["still_failing"][0]["match"] == "relaxed"


def test_verdict_improved_when_existing_blockers_resolve_without_new_issues() -> None:
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

    comparison = compare_verification_runs(baseline, candidate).to_dict()

    assert comparison["verdict"] == "improved"
    assert comparison["summary"]["blocking_before"] == 2
    assert comparison["summary"]["blocking_after"] == 0
    assert comparison["summary"]["resolved_count"] == 2
    assert comparison["summary"]["new_issue_count"] == 0


def test_verdict_regressed_when_candidate_introduces_only_new_blockers() -> None:
    baseline = verification_run(
        "baseline",
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
    candidate = verification_run(
        "candidate",
        fast_checks=[check_result("py_test", "failed", kind="test", exit_code=1)],
        deep_checks=[
            check_result(
                "sg_scan",
                "failed",
                kind="static-analysis",
                findings=[finding("rule.new", "src/new.py", 7, "New blocker")],
                blocking_findings_count=1,
            )
        ],
    )

    comparison = compare_verification_runs(baseline, candidate).to_dict()

    assert comparison["verdict"] == "regressed"
    assert ids(comparison["fast_checks"]["regressed"]) == ["py_test"]
    assert ids(comparison["deep_findings"]["newly_introduced"]) == [
        "sg_scan:rule.new:src/new.py:7"
    ]


def test_one_sided_deep_artifacts_make_verification_not_comparable() -> None:
    baseline = verification_run(
        "baseline",
        fast_checks=[],
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
    candidate = verification_run("candidate", fast_checks=[], deep_checks=None)

    comparison = compare_verification_runs(baseline, candidate).to_dict()

    assert comparison["verdict"] == "verification_failed"
    assert comparison["deep_findings"]["skipped_or_not_comparable"][0]["id"] == (
        "deep:summary"
    )


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
