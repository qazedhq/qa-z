"""Section render helpers for review packets."""

from __future__ import annotations

from typing import Any

from qa_z.artifacts import extract_candidate_files
from qa_z.reporters.deep_context import (
    DeepContext,
    format_finding_location,
    format_severity_summary,
)
from qa_z.reporters.repair_prompt import fix_priority
from qa_z.runners.models import CheckResult, RunSummary


def ordered_failed_checks(summary: RunSummary) -> list[CheckResult]:
    """Return failed or errored checks in review priority order."""
    failed = [check for check in summary.checks if check.status in {"failed", "error"}]
    return [
        check
        for _index, check in sorted(
            enumerate(failed), key=lambda item: (fix_priority(item[1]), item[0])
        )
    ]


def render_failed_check(check: CheckResult) -> list[str]:
    """Render one failed check with evidence tail."""
    lines = [
        f"### {check.id}",
        "",
        f"- Tool: {check.tool}",
        f"- Kind: {check.kind}",
        f"- Command: `{' '.join(check.command)}`",
        f"- Exit code: `{check.exit_code}`",
    ]
    candidates = extract_candidate_files(
        "\n".join(part for part in (check.stdout_tail, check.stderr_tail) if part)
    )
    if candidates:
        lines.append("- Candidate files:")
        lines.extend(f"  - `{path}`" for path in candidates)
    lines.extend(["", "Evidence:", "```text", evidence_tail(check), "```", ""])
    return lines


def check_summary(check: CheckResult) -> dict[str, Any]:
    """Render compact check metadata for review JSON."""
    return {
        "id": check.id,
        "kind": check.kind,
        "tool": check.tool,
        "command": check.command,
        "status": check.status,
        "exit_code": check.exit_code,
        "duration_ms": check.duration_ms,
        "execution_mode": check.execution_mode,
        "target_paths": check.target_paths,
        "selection_reason": check.selection_reason,
        "high_risk_reasons": check.high_risk_reasons,
    }


def failed_check_summary(check: CheckResult) -> dict[str, Any]:
    """Render failed check metadata with evidence for review JSON."""
    data = check_summary(check)
    data["stdout_tail"] = check.stdout_tail
    data["stderr_tail"] = check.stderr_tail
    data["candidate_files"] = extract_candidate_files(
        "\n".join(part for part in (check.stdout_tail, check.stderr_tail) if part)
    )
    return data


def evidence_tail(check: CheckResult) -> str:
    """Combine stdout and stderr tails for display."""
    parts = []
    if check.stdout_tail:
        parts.append(check.stdout_tail.rstrip())
    if check.stderr_tail:
        parts.append(check.stderr_tail.rstrip())
    return "\n".join(parts) if parts else "No stdout or stderr tail captured."


def render_selection_markdown(summary: RunSummary) -> list[str]:
    """Render v2 check-selection context when present."""
    if summary.selection is None:
        return []
    selection = summary.selection
    return [
        "## Check Selection",
        "",
        f"- Mode: {selection.mode}",
        f"- Input source: {selection.input_source}",
        f"- Changed files: {len(selection.changed_files)}",
        f"- Full checks: {format_check_list(selection.full_checks)}",
        f"- Targeted checks: {format_check_list(selection.targeted_checks)}",
        f"- Skipped checks: {format_check_list(selection.skipped_checks)}",
        f"- High-risk reasons: {format_check_list(selection.high_risk_reasons)}",
        "",
    ]


def format_check_list(items: list[str]) -> str:
    """Render a compact comma-separated list for review output."""
    return ", ".join(items) if items else "none"


def render_deep_findings_markdown(deep: DeepContext | None) -> list[str]:
    """Render optional deep findings for run-aware review packets."""
    if deep is None:
        return []
    lines = [
        "",
        "## Deep Findings",
        "",
        f"- Status: {deep.summary.status}",
        f"- Findings: {deep.findings_count}",
        f"- Blocking findings: {deep.blocking_findings_count}",
        f"- Filtered findings: {deep.filtered_findings_count}",
        f"- Highest severity: {deep.highest_severity or 'none'}",
        f"- Severity summary: {format_severity_summary(deep.severity_summary)}",
        f"- Affected files: {format_affected_files(deep.affected_files)}",
    ]
    lines.extend(render_scan_warning_markdown(deep))
    if deep.primary_check is not None:
        lines.append(f"- {format_deep_check_run_sentence(deep)}")
        if deep.primary_check.selection_reason:
            lines.append(f"- Selection reason: {deep.primary_check.selection_reason}")

    if deep.grouped_findings:
        lines.extend(["", "Top grouped findings:"])
        for finding in deep.grouped_findings[:5]:
            lines.append(format_grouped_finding(finding))
    elif deep.findings:
        lines.extend(["", "Top findings:"])
        for finding in deep.findings[:5]:
            lines.append(
                "- "
                f"`{format_finding_location(finding)}` "
                f"{finding['severity']} {finding['rule_id']} - {finding['message']}"
            )
    else:
        lines.extend(["", "No Semgrep findings were reported."])
    return lines


def render_scan_warning_markdown(deep: DeepContext) -> list[str]:
    """Render non-blocking deep scan-quality warnings when present."""
    if not deep.scan_warning_count and not deep.scan_quality_status:
        return []
    warning_noun = "warning" if deep.scan_warning_count == 1 else "warnings"
    status = deep.scan_quality_status or "unknown"
    return [
        f"- Scan quality: {status} ({deep.scan_warning_count} {warning_noun})",
        f"- Scan warning types: {format_check_list(deep.scan_warning_types)}",
        f"- Scan warning paths: {format_affected_files(deep.scan_warning_paths)}",
        f"- Scan warning checks: {format_check_list(deep.scan_warning_check_ids)}",
    ]


def format_deep_check_run_sentence(deep: DeepContext) -> str:
    """Render the primary deep check execution mode in one sentence."""
    check_id = deep.primary_check.id if deep.primary_check else "deep check"
    mode = deep.execution_mode
    if deep.target_count:
        noun = "file" if deep.target_count == 1 else "files"
        return f"`{check_id}` ran in {mode} mode for {deep.target_count} {noun}"
    return f"`{check_id}` ran in {mode} mode"


def format_affected_files(paths: list[str]) -> str:
    """Render affected files for Markdown."""
    if not paths:
        return "none"
    return ", ".join(f"`{path}`" for path in paths)


def format_grouped_finding(finding: dict[str, Any]) -> str:
    """Render one grouped Semgrep finding for review packets."""
    count = int(finding.get("count") or 1)
    occurrence = "occurrence" if count == 1 else "occurrences"
    location = format_finding_location(finding)
    return (
        "- "
        f"`{finding.get('rule_id', 'unknown')}` in `{location}` "
        f"({count} {occurrence}) - {finding.get('message', '')}"
    )
