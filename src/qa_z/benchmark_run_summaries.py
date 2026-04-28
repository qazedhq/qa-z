"""Run-oriented benchmark actual-summary helpers."""

from __future__ import annotations

from typing import Any

from qa_z.benchmark_helpers import (
    aggregate_filter_reasons,
    coerce_mapping,
    unique_strings,
)
from qa_z.repair_handoff import RepairHandoffPacket
from qa_z.runners.models import RunSummary
from qa_z.verification import VERIFY_SCHEMA_VERSION


def summarize_fast_actual(summary: RunSummary) -> dict[str, Any]:
    """Return benchmark-relevant fast-run observations."""
    failed_checks = [
        check.id for check in summary.checks if check.status in {"failed", "error"}
    ]
    return {
        "status": summary.status,
        "schema_version": summary.schema_version,
        "failed_checks": failed_checks,
        "blocking_failed_checks": failed_checks,
        "passed_checks": [
            check.id for check in summary.checks if check.status == "passed"
        ],
        "warning_checks": [
            check.id for check in summary.checks if check.status == "warning"
        ],
        "totals": summary.totals,
    }


def summarize_deep_actual(summary: RunSummary) -> dict[str, Any]:
    """Return benchmark-relevant deep-run observations."""
    blocking = sum(check.blocking_findings_count or 0 for check in summary.checks)
    findings = sum(check.findings_count or 0 for check in summary.checks)
    filtered = sum(check.filtered_findings_count or 0 for check in summary.checks)
    grouped = sum(len(check.grouped_findings) for check in summary.checks)
    scan_warning_count = sum(check.scan_warning_count or 0 for check in summary.checks)
    filter_reasons = aggregate_filter_reasons(summary.checks)
    diagnostics = coerce_mapping(summary.diagnostics)
    scan_quality = coerce_mapping(diagnostics.get("scan_quality"))
    scan_warnings = [
        warning
        for check in summary.checks
        for warning in check.scan_warnings
        if isinstance(warning, dict)
    ]
    run_resolution = coerce_mapping(summary.run_resolution)
    error_types = unique_strings(
        [str(check.error_type or "") for check in summary.checks]
    )
    rule_ids = unique_strings(
        [
            str(finding.get("rule_id") or "")
            for check in summary.checks
            for finding in [*check.findings, *check.grouped_findings]
            if isinstance(finding, dict)
        ]
    )
    return {
        "status": summary.status,
        "schema_version": summary.schema_version,
        "findings": findings,
        "findings_count": findings,
        "blocking_findings": blocking,
        "blocking_findings_count": blocking,
        "filtered_findings_count": filtered,
        "grouped_findings_count": grouped,
        "filter_reasons": filter_reasons,
        "rule_ids": rule_ids,
        "scan_warning_count": scan_warning_count,
        "scan_warning_types": unique_strings(
            [str(warning.get("error_type") or "") for warning in scan_warnings]
        ),
        "scan_warning_paths": unique_strings(
            [str(warning.get("path") or "") for warning in scan_warnings]
        ),
        "scan_quality_status": scan_quality.get("status"),
        "scan_quality_warning_count": scan_quality.get("warning_count"),
        "scan_quality_warning_types": list(scan_quality.get("warning_types") or []),
        "scan_quality_warning_paths": list(scan_quality.get("warning_paths") or []),
        "scan_quality_check_ids": list(scan_quality.get("check_ids") or []),
        "run_resolution_source": run_resolution.get("source"),
        "attached_to_fast_run": run_resolution.get("attached_to_fast_run"),
        "run_resolution_fast_summary_path": run_resolution.get("fast_summary_path"),
        "error_types": error_types,
        "config_error": "semgrep_config_error" in error_types,
        "policy": dict(summary.policy),
    }


def summarize_handoff_actual(handoff: RepairHandoffPacket) -> dict[str, Any]:
    """Return benchmark-relevant repair handoff observations."""
    data = handoff.to_dict()
    repair = coerce_mapping(data.get("repair"))
    validation = coerce_mapping(data.get("validation"))
    targets = [
        dict(target) for target in repair.get("targets", []) if isinstance(target, dict)
    ]
    commands = [
        dict(command)
        for command in validation.get("commands", [])
        if isinstance(command, dict)
    ]
    return {
        "kind": data.get("kind"),
        "schema_version": data.get("schema_version"),
        "repair_needed": repair.get("repair_needed"),
        "target_ids": [str(target.get("id")) for target in targets],
        "target_sources": unique_strings(
            [str(target.get("source") or "") for target in targets]
        ),
        "affected_files": list(repair.get("affected_files") or []),
        "validation_command_ids": [str(command.get("id")) for command in commands],
    }


def summarize_verify_actual(comparison: dict[str, Any]) -> dict[str, Any]:
    """Return benchmark-relevant verification observations."""
    summary = coerce_mapping(comparison.get("summary"))
    return {
        "schema_version": VERIFY_SCHEMA_VERSION,
        "verdict": comparison.get("verdict"),
        "blocking_before": summary.get("blocking_before"),
        "blocking_after": summary.get("blocking_after"),
        "resolved_count": summary.get("resolved_count"),
        "remaining_issue_count": summary.get(
            "remaining_issue_count", summary.get("still_failing_count")
        ),
        "new_issue_count": summary.get("new_issue_count"),
        "regression_count": summary.get("regression_count"),
        "not_comparable_count": summary.get("not_comparable_count"),
    }


def summarize_verify_summary_actual(summary: dict[str, Any]) -> dict[str, Any]:
    """Return benchmark-relevant observations from verify/summary.json."""
    return {
        "schema_version": summary.get("schema_version", VERIFY_SCHEMA_VERSION),
        "verdict": summary.get("verdict"),
        "blocking_before": summary.get("blocking_before"),
        "blocking_after": summary.get("blocking_after"),
        "resolved_count": summary.get("resolved_count"),
        "remaining_issue_count": summary.get(
            "remaining_issue_count", summary.get("still_failing_count")
        ),
        "new_issue_count": summary.get("new_issue_count"),
        "regression_count": summary.get("regression_count"),
        "not_comparable_count": summary.get("not_comparable_count"),
    }
