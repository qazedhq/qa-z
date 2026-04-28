from __future__ import annotations

from qa_z.verification_models import (
    FastCheckDelta,
    VerificationCategory,
    VerificationFindingDelta,
)
from tests.verification_test_support import verification_run

import qa_z.verification_comparison_builder as builder_module


def test_build_verification_comparison_derives_summary_and_verdict(monkeypatch) -> None:
    baseline = verification_run("baseline", fast_checks=[])
    candidate = verification_run("candidate", fast_checks=[])
    fast_checks: dict[VerificationCategory, list[FastCheckDelta]] = {
        "resolved": [
            FastCheckDelta(
                id="py_test",
                classification="resolved",
                baseline_status="failed",
                candidate_status="passed",
                baseline_exit_code=1,
                candidate_exit_code=0,
            )
        ],
        "still_failing": [],
        "regressed": [],
        "newly_introduced": [],
        "skipped_or_not_comparable": [],
    }
    deep_findings: dict[VerificationCategory, list[VerificationFindingDelta]] = {
        "resolved": [],
        "still_failing": [],
        "regressed": [],
        "newly_introduced": [],
        "skipped_or_not_comparable": [],
    }
    monkeypatch.setattr(
        builder_module,
        "build_comparison_summary",
        lambda **kwargs: {
            "blocking_before": 1,
            "blocking_after": 0,
            "resolved_count": 1,
            "new_issue_count": 0,
        },
    )
    monkeypatch.setattr(builder_module, "derive_verdict", lambda summary: "improved")

    comparison = builder_module.build_verification_comparison(
        baseline=baseline,
        candidate=candidate,
        fast_checks=fast_checks,
        deep_findings=deep_findings,
    )

    assert comparison.verdict == "improved"
    assert comparison.summary["resolved_count"] == 1
    assert comparison.fast_checks is fast_checks
    assert comparison.deep_findings is deep_findings
