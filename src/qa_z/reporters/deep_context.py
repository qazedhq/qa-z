"""Shared helpers for consuming sibling deep-run summaries."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

from qa_z.artifacts import ArtifactLoadError, RunSource, load_run_summary
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
TOP_FINDINGS_LIMIT = 5


@dataclass(frozen=True)
class DeepContext:
    """Compact view of deep findings for human and JSON consumers."""

    summary: RunSummary
    primary_check: CheckResult | None
    findings: list[dict[str, Any]]
    grouped_findings: list[dict[str, Any]]
    findings_count: int
    blocking_findings_count: int
    filtered_findings_count: int
    filter_reasons: dict[str, int]
    severity_summary: dict[str, int]
    affected_files: list[str]
    highest_severity: str | None
    policy: dict[str, Any]

    @property
    def execution_mode(self) -> str:
        """Return the first deep check execution mode, or a stable fallback."""
        if self.primary_check and self.primary_check.execution_mode:
            return self.primary_check.execution_mode
        if self.summary.selection and self.summary.selection.skipped_checks:
            return "skipped"
        if self.summary.selection and self.summary.selection.targeted_checks:
            return "targeted"
        if self.summary.selection and self.summary.selection.full_checks:
            return "full"
        return "none"

    @property
    def target_count(self) -> int:
        """Return the primary check target-path count."""
        if not self.primary_check:
            return 0
        return len(self.primary_check.target_paths)

    def to_dict(self) -> dict[str, Any]:
        """Render this deep context as JSON-safe data."""
        return {
            "status": self.summary.status,
            "summary_path": self.summary.artifact_dir,
            "selection": (
                self.summary.selection.to_dict()
                if self.summary.selection is not None
                else None
            ),
            "findings_count": self.findings_count,
            "blocking_findings_count": self.blocking_findings_count,
            "filtered_findings_count": self.filtered_findings_count,
            "filter_reasons": self.filter_reasons,
            "severity_summary": self.severity_summary,
            "highest_severity": self.highest_severity,
            "affected_files": self.affected_files,
            "execution_mode": self.execution_mode,
            "target_paths": (
                self.primary_check.target_paths if self.primary_check else []
            ),
            "top_findings": self.findings[:TOP_FINDINGS_LIMIT],
            "top_grouped_findings": self.grouped_findings[:TOP_FINDINGS_LIMIT],
            "policy": self.policy,
        }


def load_sibling_deep_summary(run_source: RunSource) -> RunSummary | None:
    """Load ``deep/summary.json`` beside a fast run when it exists."""
    summary_path = run_source.run_dir / "deep" / "summary.json"
    if not summary_path.is_file():
        return None
    summary = load_run_summary(summary_path)
    if summary.mode != "deep":
        raise ArtifactLoadError(f"Expected a deep summary at {summary_path}.")
    return summary


def build_deep_context(summary: RunSummary | None) -> DeepContext | None:
    """Build a compact deep context, returning ``None`` when no deep run exists."""
    if summary is None:
        return None

    primary_check = summary.checks[0] if summary.checks else None
    findings = [
        normalize_finding(finding)
        for check in summary.checks
        for finding in check.findings
        if isinstance(finding, dict)
    ]
    grouped_findings = [
        normalize_grouped_finding(finding)
        for check in summary.checks
        for finding in check.grouped_findings
        if isinstance(finding, dict)
    ]
    severity_summary = aggregate_severities(summary.checks, findings)
    display_findings = grouped_findings or findings
    affected_files = unique_preserve_order(
        [
            str(finding.get("path", "")).strip()
            for finding in display_findings
            if str(finding.get("path", "")).strip()
        ]
    )
    findings_count = (
        sum(check.findings_count or 0 for check in summary.checks)
        if summary.checks
        else 0
    )
    if findings and findings_count < len(findings):
        findings_count = len(findings)
    blocking_findings_count = sum(
        infer_blocking_count(check) for check in summary.checks
    )
    filtered_findings_count = sum(
        check.filtered_findings_count or 0 for check in summary.checks
    )
    filter_reasons = aggregate_filter_reasons(summary.checks)
    policy = primary_policy(summary, primary_check)

    return DeepContext(
        summary=summary,
        primary_check=primary_check,
        findings=findings,
        grouped_findings=grouped_findings,
        findings_count=findings_count,
        blocking_findings_count=blocking_findings_count,
        filtered_findings_count=filtered_findings_count,
        filter_reasons=filter_reasons,
        severity_summary=severity_summary,
        affected_files=affected_files,
        highest_severity=highest_severity(severity_summary),
        policy=policy,
    )


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


def normalize_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Return a stable finding mapping for renderer consumption."""
    return {
        "rule_id": str(finding.get("rule_id") or "unknown"),
        "severity": str(finding.get("severity") or "UNKNOWN"),
        "path": str(finding.get("path") or ""),
        "line": finding.get("line"),
        "message": str(finding.get("message") or ""),
    }


def normalize_grouped_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Return a stable grouped finding mapping for renderer consumption."""
    return {
        "rule_id": str(finding.get("rule_id") or "unknown"),
        "severity": str(finding.get("severity") or "UNKNOWN"),
        "path": str(finding.get("path") or ""),
        "count": coerce_count(finding.get("count")),
        "representative_line": finding.get("representative_line"),
        "message": str(finding.get("message") or ""),
    }


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


def format_severity_summary(severity_summary: dict[str, int]) -> str:
    """Render severity counts in a compact deterministic order."""
    if not severity_summary:
        return "none"
    return ", ".join(
        f"{severity}: {count}" for severity, count in severity_summary.items()
    )


def format_finding_location(finding: dict[str, Any]) -> str:
    """Render ``path`` or ``path:line`` for a finding."""
    path = str(finding.get("path") or "unknown")
    line = finding.get("line", finding.get("representative_line"))
    return f"{path}:{line}" if line else path


def coerce_count(value: Any) -> int:
    """Return a positive occurrence count for grouped findings."""
    try:
        count = int(value)
    except (TypeError, ValueError):
        return 1
    return count if count > 0 else 1


def unique_preserve_order(items: list[str]) -> list[str]:
    """Return unique strings in first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
