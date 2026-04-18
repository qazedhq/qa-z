"""Render compact Markdown for GitHub Actions job summaries."""

from __future__ import annotations

from pathlib import Path

from qa_z.artifacts import RunSource, format_path
from qa_z.reporters.deep_context import (
    DeepContext,
    build_deep_context,
    format_finding_location,
)
from qa_z.reporters.verification_publish import (
    SessionPublishSummary,
    VerificationPublishSummary,
    render_publish_summary_markdown,
)
from qa_z.runners.models import CheckResult, RunSummary


MAX_CHANGED_FILES = 12


def render_github_summary(
    *,
    summary: RunSummary,
    run_source: RunSource,
    root: Path,
    deep_summary: RunSummary | None = None,
    publish_summary: VerificationPublishSummary | SessionPublishSummary | None = None,
) -> str:
    """Render a compact QA-Z run summary for GitHub Actions."""
    selection_mode = summary.selection.mode if summary.selection is not None else "none"
    deep_context = build_deep_context(deep_summary)
    deep_status = deep_summary.status if deep_summary is not None else "not run"
    lines = [
        "# QA-Z Summary",
        "",
        f"**Fast:** {summary.status}",
        f"**Deep:** {deep_status}",
        f"**Selection:** {selection_mode}",
        f"**Contract:** `{summary.contract_path or 'none'}`",
        "",
        "## Fast QA",
        "",
        f"- Passed: {summary.totals['passed']}",
        f"- Failed: {summary.totals['failed']}",
        f"- Skipped: {summary.totals['skipped']}",
        f"- Warning: {summary.totals['warning']}",
        "",
        "## Failed Checks",
        "",
    ]
    failed_checks = [
        check for check in summary.checks if check.status in {"failed", "error"}
    ]
    if not failed_checks:
        lines.append("- No failed checks.")
    else:
        lines.extend(render_failed_check(check) for check in failed_checks)

    lines.extend(["", "## Changed Files", ""])
    lines.extend(render_changed_files(summary))

    lines.extend(["", "## Selection", ""])
    lines.extend(render_selection(summary))

    lines.extend(render_deep_qa(deep_context))
    if publish_summary is not None:
        lines.extend(
            ["", *render_publish_summary_markdown(publish_summary).splitlines()]
        )

    lines.extend(
        [
            "",
            "## Next",
            "",
            f"- Fast summary: `{format_path(run_source.summary_path, root)}`",
            f"- Review packet: `{format_path(run_source.run_dir / 'review' / 'review.md', root)}`",
            f"- Repair prompt: `{format_path(run_source.run_dir / 'repair' / 'prompt.md', root)}`",
        ]
    )
    return "\n".join(lines).strip() + "\n"


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


def coerce_count(value: object) -> int:
    """Return a positive grouped finding count."""
    try:
        count = int(str(value)) if value is not None else 1
    except (TypeError, ValueError):
        return 1
    return count if count > 0 else 1
