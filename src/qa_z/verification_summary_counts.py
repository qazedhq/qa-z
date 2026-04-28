"""Count helpers for verification summaries."""

from __future__ import annotations

from qa_z.runners.models import CheckResult, RunSummary
from qa_z.verification_finding_support import extract_deep_findings


def count_blocking_checks(summary: RunSummary) -> int:
    return sum(1 for check in summary.checks if is_blocking_check(check))


def count_blocking_deep_findings(summary: RunSummary | None) -> int:
    if summary is None:
        return 0
    extracted = extract_deep_findings(summary)
    if extracted:
        return sum(1 for finding in extracted if finding.blocking)
    return sum(max(check.blocking_findings_count or 0, 0) for check in summary.checks)


def count_deep_findings(summary: RunSummary | None) -> int:
    if summary is None:
        return 0
    extracted = extract_deep_findings(summary)
    if extracted:
        return len(extracted)
    return sum(check.findings_count or 0 for check in summary.checks)


def is_blocking_check(check: CheckResult | None) -> bool:
    return bool(check is not None and check.status in {"failed", "error"})
