from __future__ import annotations

import json

import qa_z.verification_outcome_render as render_module
import qa_z.verification_outcome_summary as summary_module
from tests.verification_test_support import check_result, verification_run
from qa_z.verification import compare_verification_runs


def test_verification_outcome_helpers_render_summary_exit_code_and_json() -> None:
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

    assert summary_module.verification_summary_dict(comparison) == {
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
    assert summary_module.verify_exit_code(comparison.verdict) == 0
    payload = json.loads(render_module.comparison_json(comparison))
    assert payload["verdict"] == "improved"
    assert payload["summary"]["resolved_count"] == 1


def test_verify_exit_code_pins_non_improved_verdicts() -> None:
    assert summary_module.verify_exit_code("unchanged") == 1
    assert summary_module.verify_exit_code("regressed") == 1
    assert summary_module.verify_exit_code("verification_failed") == 2
