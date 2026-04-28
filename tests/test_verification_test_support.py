from __future__ import annotations

import tests.verification_test_support as support_module


def test_verification_test_support_builds_run_and_finding_helpers() -> None:
    run = support_module.verification_run(
        "candidate",
        fast_checks=[support_module.check_result("py_test", "passed", exit_code=0)],
        deep_checks=[
            support_module.check_result(
                "sg_scan",
                "failed",
                kind="static-analysis",
                findings=[
                    support_module.finding("rule.one", "src/app.py", 7, "Blocker")
                ],
                blocking_findings_count=1,
            )
        ],
    )

    assert run.run_id == "candidate"
    assert run.fast_summary.mode == "fast"
    assert run.deep_summary is not None
    assert run.deep_summary.checks[0].findings[0]["rule_id"] == "rule.one"


def test_verification_test_support_builds_count_only_deep_runs() -> None:
    run = support_module.count_only_deep_run(
        "candidate",
        findings_count=3,
        blocking_findings_count=2,
    )

    assert run.deep_summary is not None
    check = run.deep_summary.checks[0]
    assert check.findings_count == 3
    assert check.blocking_findings_count == 2
    assert check.findings == []
