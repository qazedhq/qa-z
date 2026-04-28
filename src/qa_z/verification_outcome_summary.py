"""Summary helpers for verification outcomes."""

from __future__ import annotations

from typing import Any

from qa_z.verification_models import VerificationComparison


def verification_summary_dict(comparison: VerificationComparison) -> dict[str, Any]:
    summary = comparison.summary
    return {
        "kind": "qa_z.verify_summary",
        "schema_version": 1,
        "repair_improved": comparison.verdict == "improved",
        "verdict": comparison.verdict,
        "blocking_before": summary["blocking_before"],
        "blocking_after": summary["blocking_after"],
        "resolved_count": summary["resolved_count"],
        "remaining_issue_count": summary["still_failing_count"],
        "new_issue_count": summary["new_issue_count"],
        "regression_count": summary["regression_count"],
        "not_comparable_count": summary["not_comparable_count"],
    }


def verify_exit_code(verdict: str) -> int:
    if verdict == "improved":
        return 0
    if verdict == "verification_failed":
        return 2
    return 1
