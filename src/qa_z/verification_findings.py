"""Deep-finding comparison helpers for verification."""

from __future__ import annotations

from qa_z.runners.models import RunSummary
from collections.abc import Sequence
from qa_z.verification_finding_compare_support import empty_categories
from qa_z.verification_finding_matching import compare_extracted_findings
from qa_z.verification_finding_support import extract_deep_findings
from qa_z.verification_models import (
    VerificationCategory,
    VerificationFinding,
    VerificationFindingDelta,
)


def compare_deep_findings_impl(
    baseline_summary: RunSummary | None, candidate_summary: RunSummary | None
) -> dict[VerificationCategory, list[VerificationFindingDelta]]:
    """Classify deep finding changes using strict then relaxed matching."""
    categories = empty_categories()
    if baseline_summary is None and candidate_summary is None:
        return categories
    if baseline_summary is None or candidate_summary is None:
        categories["skipped_or_not_comparable"].append(
            VerificationFindingDelta(
                id="deep:summary",
                classification="skipped_or_not_comparable",
                source="deep",
                rule_id="summary",
                path="",
                line=None,
                message=(
                    "Deep comparison requires both baseline and candidate "
                    "deep/summary.json artifacts, or neither."
                ),
            )
        )
        return categories

    baseline_findings = extract_deep_findings(baseline_summary)
    candidate_findings = extract_deep_findings(candidate_summary)
    if _has_compact_deep_counts_without_details(
        baseline_summary, baseline_findings
    ) or _has_compact_deep_counts_without_details(
        candidate_summary, candidate_findings
    ):
        categories["skipped_or_not_comparable"].append(
            VerificationFindingDelta(
                id="deep:summary",
                classification="skipped_or_not_comparable",
                source="deep",
                rule_id="summary",
                path="",
                line=None,
                message=(
                    "Deep comparison requires detailed findings when only compact "
                    "findings_count/blocking_findings_count artifacts are available."
                ),
            )
        )
        return categories
    return compare_extracted_findings(
        baseline_findings=baseline_findings,
        candidate_findings=candidate_findings,
    )


def _has_compact_deep_counts_without_details(
    summary: RunSummary | None, extracted_findings: Sequence[VerificationFinding]
) -> bool:
    if summary is None or extracted_findings:
        return False
    return any(
        (check.findings_count or 0) > 0 or (check.blocking_findings_count or 0) > 0
        for check in summary.checks
    )


__all__ = ["compare_deep_findings_impl"]
