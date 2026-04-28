"""Shared helpers for consuming sibling deep-run summaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qa_z.artifacts import ArtifactLoadError, RunSource, load_run_summary
from qa_z.reporters.deep_context_findings import (
    coerce_count,
    normalize_finding,
    normalize_grouped_finding,
    unique_preserve_order,
)
from qa_z.reporters.deep_context_formatting import (
    format_finding_location,
    format_severity_summary,
)
from qa_z.reporters.deep_context_loading import (
    build_deep_context,
    load_sibling_deep_summary,
)
from qa_z.reporters.deep_context_summary import (
    aggregate_filter_reasons,
    aggregate_severities,
    highest_severity,
    infer_blocking_count,
    primary_policy,
    severity_sort_key,
)
from qa_z.runners.models import CheckResult, RunSummary

TOP_FINDINGS_LIMIT = 5

__all__ = [
    "DeepContext",
    "TOP_FINDINGS_LIMIT",
    "aggregate_filter_reasons",
    "aggregate_severities",
    "build_deep_context",
    "coerce_count",
    "format_finding_location",
    "format_severity_summary",
    "highest_severity",
    "infer_blocking_count",
    "load_sibling_deep_summary",
    "normalize_finding",
    "normalize_grouped_finding",
    "primary_policy",
    "severity_sort_key",
    "unique_preserve_order",
]


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


def _load_sibling_deep_summary_impl(run_source: RunSource) -> RunSummary | None:
    """Load ``deep/summary.json`` beside a fast run when it exists."""
    summary_path = run_source.run_dir / "deep" / "summary.json"
    if not summary_path.is_file():
        return None
    summary = load_run_summary(summary_path)
    if summary.mode != "deep":
        raise ArtifactLoadError(f"Expected a deep summary at {summary_path}.")
    return summary


def _build_deep_context_impl(summary: RunSummary | None) -> DeepContext | None:
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


def _format_severity_summary_impl(severity_summary: dict[str, int]) -> str:
    """Render severity counts in a compact deterministic order."""
    if not severity_summary:
        return "none"
    return ", ".join(
        f"{severity}: {count}" for severity, count in severity_summary.items()
    )


def _format_finding_location_impl(finding: dict[str, Any]) -> str:
    """Render ``path`` or ``path:line`` for a finding."""
    path = str(finding.get("path") or "unknown")
    line = finding.get("line", finding.get("representative_line"))
    return f"{path}:{line}" if line else path
