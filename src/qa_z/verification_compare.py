"""Verification comparison helpers."""

from __future__ import annotations

from qa_z.runners.models import RunSummary
from qa_z.verification_comparison_builder import build_verification_comparison
from qa_z.verification_fast_compare import compare_fast_checks
from qa_z.verification_findings import compare_deep_findings_impl
from qa_z.verification_models import (
    VerificationCategory,
    VerificationFindingDelta,
    VerificationRun,
)


def compare_verification_runs(baseline: VerificationRun, candidate: VerificationRun):
    """Compare baseline and candidate QA-Z run evidence."""
    fast_checks = compare_fast_checks(
        baseline.fast_summary.checks, candidate.fast_summary.checks
    )
    deep_findings = compare_deep_findings(baseline.deep_summary, candidate.deep_summary)
    return build_verification_comparison(
        baseline=baseline,
        candidate=candidate,
        fast_checks=fast_checks,
        deep_findings=deep_findings,
    )


def compare_deep_findings(
    baseline_summary: RunSummary | None, candidate_summary: RunSummary | None
) -> dict[VerificationCategory, list[VerificationFindingDelta]]:
    """Compare deep finding sets from baseline and candidate runs."""
    return compare_deep_findings_impl(baseline_summary, candidate_summary)


__all__ = [
    "compare_deep_findings",
    "compare_fast_checks",
    "compare_verification_runs",
]
