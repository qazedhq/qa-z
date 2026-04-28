"""Render compact Markdown for GitHub Actions job summaries."""

from __future__ import annotations

from pathlib import Path

from qa_z.artifacts import RunSource, format_path
from qa_z.reporters.deep_context import build_deep_context
from qa_z.reporters.github_summary_render import render_github_summary
from qa_z.reporters.github_summary_sections import (
    coerce_count,
    format_code_list,
    format_grouped_finding,
    render_changed_files,
    render_deep_qa,
    render_failed_check,
    render_selection,
)
from qa_z.reporters.verification_publish import (
    SessionPublishSummary,
    VerificationPublishSummary,
    render_publish_summary_markdown,
)
from qa_z.runners.models import RunSummary

__all__ = [
    "coerce_count",
    "format_code_list",
    "format_grouped_finding",
    "render_changed_files",
    "render_deep_qa",
    "render_failed_check",
    "render_github_summary",
    "render_selection",
]


def _render_github_summary_impl(
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
