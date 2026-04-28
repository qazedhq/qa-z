"""Summary aggregation helpers for deep-context summaries."""

from __future__ import annotations

from collections import Counter
from typing import Any

from qa_z.runners.models import CheckResult, RunSummary

SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "ERROR": 2,
    "MEDIUM": 3,
    "WARNING": 4,
    "LOW": 5,
    "INFO": 6,
    "UNKNOWN": 7,
}


def aggregate_severities(
    checks: list[CheckResult], findings: list[dict[str, Any]]
) -> dict[str, int]:
    """Aggregate check severity summaries, falling back to finding data."""
    counts: Counter[str] = Counter()
    for check in checks:
        counts.update(
            {str(key): int(value) for key, value in check.severity_summary.items()}
        )
    if not counts:
        counts.update(str(finding.get("severity") or "UNKNOWN") for finding in findings)
    return dict(sorted(counts.items(), key=lambda item: severity_sort_key(item[0])))


def aggregate_filter_reasons(checks: list[CheckResult]) -> dict[str, int]:
    """Aggregate per-check Semgrep filter reasons."""
    counts: Counter[str] = Counter()
    for check in checks:
        counts.update(
            {str(key): int(value) for key, value in check.filter_reasons.items()}
        )
    return dict(sorted(counts.items()))


def infer_blocking_count(check: CheckResult) -> int:
    """Return persisted blocking count, with legacy artifact fallback."""
    if check.blocking_findings_count is not None:
        return check.blocking_findings_count
    if check.status == "failed":
        if check.findings:
            return len(check.findings)
        return check.findings_count or 0
    return 0


def primary_policy(
    summary: RunSummary, primary_check: CheckResult | None
) -> dict[str, Any]:
    """Return the primary Semgrep policy from check or summary metadata."""
    if primary_check and primary_check.policy:
        return dict(primary_check.policy)
    return dict(summary.policy)


def highest_severity(severity_summary: dict[str, int]) -> str | None:
    """Return the highest severity present in the summary."""
    present = [severity for severity, count in severity_summary.items() if count > 0]
    if not present:
        return None
    return sorted(present, key=severity_sort_key)[0]


def severity_sort_key(severity: str) -> tuple[int, str]:
    """Sort known severities from highest to lowest risk."""
    normalized = severity.upper()
    return (SEVERITY_ORDER.get(normalized, len(SEVERITY_ORDER)), normalized)
