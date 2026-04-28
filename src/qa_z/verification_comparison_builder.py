"""Builder helpers for verification comparison objects."""

from __future__ import annotations

from qa_z.verification_models import (
    FastCheckDelta,
    VerificationCategory,
    VerificationComparison,
    VerificationFindingDelta,
    VerificationRun,
)
from qa_z.verification_status import build_comparison_summary, derive_verdict


def build_verification_comparison(
    *,
    baseline: VerificationRun,
    candidate: VerificationRun,
    fast_checks: dict[VerificationCategory, list[FastCheckDelta]],
    deep_findings: dict[VerificationCategory, list[VerificationFindingDelta]],
) -> VerificationComparison:
    summary = build_comparison_summary(
        baseline=baseline,
        candidate=candidate,
        fast_checks=fast_checks,
        deep_findings=deep_findings,
    )
    verdict = derive_verdict(summary)
    return VerificationComparison(
        baseline=baseline,
        candidate=candidate,
        verdict=verdict,
        fast_checks=fast_checks,
        deep_findings=deep_findings,
        summary=summary,
    )
