"""Matching helpers for extracted verification findings."""

from __future__ import annotations

from qa_z.verification_finding_compare_support import (
    classify_matched_finding,
    empty_categories,
    finding_delta,
)
from qa_z.verification_finding_support import find_matching_candidate
from qa_z.verification_models import (
    VerificationCategory,
    VerificationFinding,
    VerificationFindingDelta,
)


def compare_extracted_findings(
    *,
    baseline_findings: list[VerificationFinding],
    candidate_findings: list[VerificationFinding],
) -> dict[VerificationCategory, list[VerificationFindingDelta]]:
    categories = empty_categories()
    matched_candidate_indexes: set[int] = set()
    for baseline in baseline_findings:
        candidate_index, match_kind = find_matching_candidate(
            baseline,
            candidate_findings,
            matched_candidate_indexes,
        )
        if candidate_index is None:
            if baseline.blocking:
                categories["resolved"].append(
                    finding_delta(
                        "resolved",
                        baseline=baseline,
                        candidate=None,
                        match="none",
                    )
                )
            continue
        matched_candidate_indexes.add(candidate_index)
        candidate = candidate_findings[candidate_index]
        classification = classify_matched_finding(baseline, candidate)
        if classification is None:
            continue
        categories[classification].append(
            finding_delta(
                classification,
                baseline=baseline,
                candidate=candidate,
                match=match_kind,
            )
        )
    for index, candidate in enumerate(candidate_findings):
        if index in matched_candidate_indexes or not candidate.blocking:
            continue
        categories["newly_introduced"].append(
            finding_delta(
                "newly_introduced",
                baseline=None,
                candidate=candidate,
                match="none",
            )
        )
    return categories
