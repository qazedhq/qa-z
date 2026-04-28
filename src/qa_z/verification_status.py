"""Summary and verdict helpers for verification."""

from __future__ import annotations

from qa_z.verification_models import (
    FastCheckDelta,
    VerificationCategory,
    VerificationFindingDelta,
    VerificationRun,
    VerificationVerdict,
)
from qa_z.verification_summary_counts import (
    count_blocking_checks,
    count_blocking_deep_findings,
    count_deep_findings,
)


def build_comparison_summary(
    *,
    baseline: VerificationRun,
    candidate: VerificationRun,
    fast_checks: dict[VerificationCategory, list[FastCheckDelta]],
    deep_findings: dict[VerificationCategory, list[VerificationFindingDelta]],
) -> dict[str, int]:
    """Build compact numeric summary data for verdict derivation."""
    fast_before = count_blocking_checks(baseline.fast_summary)
    fast_after = count_blocking_checks(candidate.fast_summary)
    deep_before = count_blocking_deep_findings(baseline.deep_summary)
    deep_after = count_blocking_deep_findings(candidate.deep_summary)
    regression_count = len(fast_checks["regressed"]) + len(deep_findings["regressed"])
    new_issue_count = (
        regression_count
        + len(fast_checks["newly_introduced"])
        + len(deep_findings["newly_introduced"])
    )
    return {
        "blocking_before": fast_before + deep_before,
        "blocking_after": fast_after + deep_after,
        "fast_blocking_before": fast_before,
        "fast_blocking_after": fast_after,
        "deep_blocking_before": deep_before,
        "deep_blocking_after": deep_after,
        "resolved_count": len(fast_checks["resolved"]) + len(deep_findings["resolved"]),
        "still_failing_count": len(fast_checks["still_failing"])
        + len(deep_findings["still_failing"]),
        "new_issue_count": new_issue_count,
        "regression_count": regression_count,
        "not_comparable_count": len(fast_checks["skipped_or_not_comparable"])
        + len(deep_findings["skipped_or_not_comparable"]),
        "verification_error_count": sum(
            1
            for delta in deep_findings["skipped_or_not_comparable"]
            if delta.id == "deep:summary"
        ),
        "deep_findings_before": count_deep_findings(baseline.deep_summary),
        "deep_findings_after": count_deep_findings(candidate.deep_summary),
    }


def derive_verdict(summary: dict[str, int]) -> VerificationVerdict:
    """Derive the final repair verification verdict."""
    if summary.get("verification_error_count", 0) > 0:
        return "verification_failed"
    if summary["new_issue_count"] > 0 and summary["resolved_count"] > 0:
        return "mixed"
    if summary["new_issue_count"] > 0:
        return "regressed"
    if summary["resolved_count"] > 0:
        return "improved"
    return "unchanged"
