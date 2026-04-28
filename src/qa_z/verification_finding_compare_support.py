"""Support helpers for verification finding delta classification."""

from __future__ import annotations

from typing import Literal

from qa_z.verification_models import (
    VerificationCategory,
    VerificationFinding,
    VerificationFindingDelta,
)


def classify_matched_finding(
    baseline: VerificationFinding, candidate: VerificationFinding
) -> VerificationCategory | None:
    """Return the category for a matched deep finding."""
    if baseline.blocking and candidate.blocking:
        return "still_failing"
    if baseline.blocking and not candidate.blocking:
        return "resolved"
    if not baseline.blocking and candidate.blocking:
        return "regressed"
    return None


def finding_delta(
    classification: VerificationCategory,
    *,
    baseline: VerificationFinding | None,
    candidate: VerificationFinding | None,
    match: Literal["strict", "relaxed", "none"],
) -> VerificationFindingDelta:
    """Build a serialized finding delta from baseline/candidate evidence."""
    reference = candidate or baseline
    if reference is None:
        raise ValueError("A finding delta requires baseline or candidate evidence.")
    return VerificationFindingDelta(
        id=reference.id,
        classification=classification,
        source=reference.source,
        rule_id=reference.rule_id,
        path=reference.path,
        line=reference.line,
        baseline_severity=baseline.severity if baseline else None,
        candidate_severity=candidate.severity if candidate else None,
        baseline_blocking=baseline.blocking if baseline else None,
        candidate_blocking=candidate.blocking if candidate else None,
        message=reference.message,
        match=match,
    )


def empty_categories() -> dict[VerificationCategory, list[VerificationFindingDelta]]:
    """Return the stable verification finding category buckets."""
    return {
        "resolved": [],
        "still_failing": [],
        "regressed": [],
        "newly_introduced": [],
        "skipped_or_not_comparable": [],
    }
