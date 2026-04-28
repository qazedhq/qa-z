"""Comparison-scenario tests for post-repair verification."""

from __future__ import annotations

from qa_z.verification import compare_verification_runs
from tests.verification_test_support import (
    check_result,
    count_only_deep_run,
    finding,
    verification_run,
)


def ids(items: list[dict[str, object]]) -> list[str]:
    """Return item ids from serialized delta records."""
    return [str(item["id"]) for item in items]


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


def test_count_only_deep_artifacts_force_not_comparable_verification() -> None:
    baseline = count_only_deep_run(
        "baseline",
        findings_count=3,
        blocking_findings_count=2,
    )
    candidate = count_only_deep_run(
        "candidate",
        findings_count=1,
        blocking_findings_count=1,
    )

    comparison = compare_verification_runs(baseline, candidate).to_dict()

    assert comparison["verdict"] == "verification_failed"
    assert comparison["summary"]["deep_blocking_before"] == 2
    assert comparison["summary"]["deep_blocking_after"] == 1
    assert comparison["deep_findings"]["skipped_or_not_comparable"][0]["id"] == (
        "deep:summary"
    )
