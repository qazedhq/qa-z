"""Support helpers for verification deep-finding extraction and matching."""

from __future__ import annotations

from typing import Any, Literal

from qa_z.runners.models import CheckResult, RunSummary
from qa_z.verification_models import VerificationFinding
from qa_z.verification_support import (
    coerce_positive_int as _coerce_positive_int,
    first_nonempty as _first_nonempty,
    normalize_path as _normalize_path,
)


def find_matching_candidate(
    baseline: VerificationFinding,
    candidates: list[VerificationFinding],
    matched_candidate_indexes: set[int],
) -> tuple[int | None, Literal["strict", "relaxed", "none"]]:
    """Find a deterministic strict or relaxed candidate match."""
    strict_matches = [
        index
        for index, candidate in enumerate(candidates)
        if index not in matched_candidate_indexes
        and candidate.strict_key == baseline.strict_key
    ]
    if len(strict_matches) == 1:
        return strict_matches[0], "strict"

    relaxed_matches = [
        index
        for index, candidate in enumerate(candidates)
        if index not in matched_candidate_indexes
        and candidate.relaxed_key == baseline.relaxed_key
    ]
    if len(relaxed_matches) == 1:
        return relaxed_matches[0], "relaxed"
    return None, "none"


def extract_deep_findings(summary: RunSummary) -> list[VerificationFinding]:
    """Extract normalized active or grouped findings from a deep summary."""
    findings: list[VerificationFinding] = []
    for check in summary.checks:
        blocking = blocking_severities(summary, check)
        if check.findings:
            findings.extend(
                normalize_active_finding(raw, check=check, blocking=blocking)
                for raw in check.findings
                if isinstance(raw, dict)
            )
            continue
        findings.extend(
            normalize_grouped_finding(raw, check=check, blocking=blocking)
            for raw in check.grouped_findings
            if isinstance(raw, dict)
        )
    return findings


def normalize_active_finding(
    raw: dict[str, Any], *, check: CheckResult, blocking: set[str]
) -> VerificationFinding:
    """Normalize one active finding from a deep check."""
    severity = _first_nonempty(raw.get("severity"), "UNKNOWN").upper()
    return VerificationFinding(
        source=check.id,
        rule_id=_first_nonempty(raw.get("rule_id"), check.id, "unknown"),
        severity=severity,
        path=_normalize_path(_first_nonempty(raw.get("path"), "")),
        line=_coerce_positive_int(raw.get("line")),
        message=_first_nonempty(raw.get("message"), ""),
        blocking=severity in blocking,
    )


def normalize_grouped_finding(
    raw: dict[str, Any], *, check: CheckResult, blocking: set[str]
) -> VerificationFinding:
    """Normalize one grouped finding from a deep check."""
    severity = _first_nonempty(raw.get("severity"), "UNKNOWN").upper()
    return VerificationFinding(
        source=check.id,
        rule_id=_first_nonempty(raw.get("rule_id"), check.id, "unknown"),
        severity=severity,
        path=_normalize_path(_first_nonempty(raw.get("path"), "")),
        line=_coerce_positive_int(raw.get("representative_line")),
        message=_first_nonempty(raw.get("message"), ""),
        blocking=severity in blocking,
        grouped=True,
        occurrences=_coerce_positive_int(raw.get("count")) or 1,
    )


def blocking_severities(summary: RunSummary, check: CheckResult) -> set[str]:
    """Return configured blocking severities for a deep check."""
    policy = check.policy or summary.policy
    if not isinstance(policy, dict):
        return {"ERROR"}
    raw = policy.get("fail_on_severity")
    if not isinstance(raw, list):
        return {"ERROR"}
    severities = {str(item).strip().upper() for item in raw if str(item).strip()}
    return severities or {"ERROR"}
