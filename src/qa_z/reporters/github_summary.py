"""Render compact Markdown for GitHub Actions job summaries."""

from __future__ import annotations

from pathlib import Path

from qa_z.artifacts import RunSource, format_path
from qa_z.reporters.deep_context import build_deep_context
from qa_z.reporters.github_summary_render import render_github_summary
from qa_z.reporters.github_summary_sections import (
    artifact_status_suffix,
    coerce_count,
    format_code_list,
    format_grouped_finding,
    infer_github_verdict,
    render_changed_files,
    render_deep_qa,
    render_failed_check,
    render_selection,
    summarize_top_blocked_reason,
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
    "infer_github_verdict",
    "render_changed_files",
    "render_deep_qa",
    "render_failed_check",
    "render_github_summary",
    "render_selection",
    "summarize_top_blocked_reason",
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
    verdict = infer_github_verdict(summary, deep_context)
    top_reason = summarize_top_blocked_reason(summary, deep_context)
    lines = [
        "# QA-Z Summary",
        "",
        f"**Verdict:** {verdict}",
        f"**Top blocked reason:** {top_reason}",
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

    review_path = run_source.run_dir / "review" / "review.md"
    repair_path = run_source.run_dir / "repair" / "prompt.md"
    deep_summary_path = run_source.run_dir / "deep" / "summary.json"
    sarif_path = run_source.run_dir / "deep" / "results.sarif"
    run_path = format_path(run_source.run_dir, root)
    lines.extend(
        [
            "",
            "## Evidence and Next Commands",
            "",
            f"- Run directory: `{run_path}`",
            (
                f"- Fast summary: `{format_path(run_source.summary_path, root)}` "
                f"({artifact_status_suffix(run_source.summary_path.exists())})"
            ),
            (
                f"- Deep summary: `{format_path(deep_summary_path, root)}` "
                f"({artifact_status_suffix(deep_summary_path.exists())})"
            ),
            (
                f"- Review packet: `{format_path(review_path, root)}` "
                f"({artifact_status_suffix(review_path.exists())})"
            ),
            (
                f"- Repair prompt: `{format_path(repair_path, root)}` "
                f"({artifact_status_suffix(repair_path.exists())})"
            ),
            (
                f"- SARIF: `{format_path(sarif_path, root)}` "
                f"({artifact_status_suffix(sarif_path.exists())})"
            ),
            "",
            f"- Read local evidence: `qa-z summary --from-run {run_path}`",
            f"- Generate repair prompt: `qa-z repair-prompt --from-run {run_path} --adapter codex`",
            f"- Verify after repair: `qa-z verify --from-run {run_path}`",
            (
                "- SARIF upload requires `security-events: write` when "
                '`upload-sarif: "true"` is enabled; otherwise it is safe to skip.'
            ),
        ]
    )
    return "\n".join(lines).strip() + "\n"
