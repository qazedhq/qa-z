"""Section helpers for GitHub Actions summary rendering."""

from __future__ import annotations

from typing import Any

from qa_z.reporters.deep_context import DeepContext, format_finding_location
from qa_z.runners.models import CheckResult, RunSummary

MAX_CHANGED_FILES = 12


def render_failed_check(check: CheckResult) -> str:
    """Render one failed check in one scan-friendly line."""
    mode = check.execution_mode or "full"
    reason = check.message or check.selection_reason or default_check_summary(check)
    return f"- `{check.id}` - {mode} - {reason}"


def default_check_summary(check: CheckResult) -> str:
    """Return a short fallback summary for a failed check."""
    if check.exit_code is None:
        return f"{check.tool} did not complete successfully."
    return f"{check.tool} exited with code {check.exit_code}."


def render_changed_files(summary: RunSummary) -> list[str]:
    """Render changed files from v2 selection metadata."""
    if summary.selection is None or not summary.selection.changed_files:
        return ["- No changed-file metadata was captured."]

    changed_files = summary.selection.changed_files
    lines = [f"- `{changed.path}`" for changed in changed_files[:MAX_CHANGED_FILES]]
    remaining = len(changed_files) - MAX_CHANGED_FILES
    if remaining > 0:
        lines.append(f"- ...and {remaining} more")
    return lines


def render_selection(summary: RunSummary) -> list[str]:
    """Render compact selection groups."""
    if summary.selection is None:
        return ["- Selection metadata was not captured."]
    selection = summary.selection
    return [
        f"- Input source: {selection.input_source}",
        f"- Full: {format_code_list(selection.full_checks)}",
        f"- Targeted: {format_code_list(selection.targeted_checks)}",
        f"- Skipped: {format_code_list(selection.skipped_checks)}",
    ]


def format_code_list(items: list[str]) -> str:
    """Render check ids as inline code."""
    if not items:
        return "none"
    return ", ".join(f"`{item}`" for item in items)


def format_plain_list(items: list[str]) -> str:
    """Render a compact plain-text list."""
    return ", ".join(items) if items else "none"


def render_deep_qa(deep: DeepContext | None) -> list[str]:
    """Render optional deep QA status for GitHub summaries."""
    if deep is None:
        return []
    lines = [
        "",
        "## Deep QA",
        "",
        f"- Status: {deep.summary.status}",
        f"- Findings: {deep.findings_count}",
        f"- Blocking: {deep.blocking_findings_count}",
        f"- Filtered: {deep.filtered_findings_count}",
        f"- Highest severity: {deep.highest_severity or 'none'}",
        f"- Mode: {deep.execution_mode}",
        f"- Files affected: {len(deep.affected_files)}",
    ]
    lines.extend(render_scan_warnings(deep))
    if deep.grouped_findings:
        lines.extend(["", "### Top Deep Findings"])
        for finding in deep.grouped_findings[:3]:
            lines.append(format_grouped_finding(finding))
    elif deep.findings:
        lines.append(
            "- "
            f"`{format_finding_location(deep.findings[0])}` "
            f"{deep.findings[0]['severity']} - {deep.findings[0]['message']}"
        )
    else:
        lines.append("- No Semgrep findings were reported.")
    return lines


def render_scan_warnings(deep: DeepContext) -> list[str]:
    """Render non-blocking deep scan-quality warnings."""
    if not deep.scan_warning_count and not deep.scan_quality_status:
        return []
    warning_noun = "warning" if deep.scan_warning_count == 1 else "warnings"
    status = deep.scan_quality_status or "unknown"
    return [
        f"- Scan quality: {status} ({deep.scan_warning_count} {warning_noun})",
        f"- Warning types: {format_plain_list(deep.scan_warning_types)}",
        f"- Warning paths: {format_code_list(deep.scan_warning_paths)}",
        f"- Warning checks: {format_plain_list(deep.scan_warning_check_ids)}",
    ]


def format_grouped_finding(finding: dict[str, object]) -> str:
    """Render a grouped Semgrep finding for GitHub Job Summary."""
    count = coerce_count(finding.get("count"))
    noun = "hit" if count == 1 else "hits"
    return (
        "- "
        f"`{finding.get('rule_id', 'unknown')}` - "
        f"`{finding.get('path', 'unknown')}` - "
        f"{count} {noun}"
    )


def coerce_count(value: Any) -> int:
    """Return a positive grouped finding count."""
    try:
        count = int(str(value)) if value is not None else 1
    except (TypeError, ValueError):
        return 1
    return count if count > 0 else 1
