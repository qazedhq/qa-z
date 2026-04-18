"""Reporters for deterministic runner summaries."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.runners.models import RunSummary


def write_run_summary_artifacts(summary: RunSummary, artifact_dir: Path) -> Path:
    """Write summary JSON, Markdown, and per-check JSON artifacts."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    checks_dir = artifact_dir / "checks"
    checks_dir.mkdir(parents=True, exist_ok=True)

    summary_path = artifact_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (artifact_dir / "summary.md").write_text(
        render_summary_markdown(summary), encoding="utf-8"
    )

    for check in summary.checks:
        check_path = checks_dir / f"{check.id}.json"
        check_path.write_text(
            json.dumps(check.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return summary_path


def render_summary_markdown(summary: RunSummary) -> str:
    """Render a compact human-readable run summary."""
    mode_title = summary.mode.capitalize() if summary.mode else "Run"
    lines = [
        f"# QA-Z {mode_title} Summary",
        "",
        f"- Status: {summary.status}",
        f"- Contract: {summary.contract_path or 'none'}",
        f"- Started: {summary.started_at}",
        f"- Finished: {summary.finished_at}",
        "",
    ]
    if summary.selection is not None:
        lines.extend(
            [
                "## Selection",
                "",
                f"- Mode: {summary.selection.mode}",
                f"- Input source: {summary.selection.input_source}",
                f"- Changed files: {len(summary.selection.changed_files)}",
                f"- Full checks: {format_list(summary.selection.full_checks)}",
                f"- Targeted checks: {format_list(summary.selection.targeted_checks)}",
                f"- Skipped checks: {format_list(summary.selection.skipped_checks)}",
                f"- High-risk reasons: {format_list(summary.selection.high_risk_reasons)}",
                "",
            ]
        )
    lines.extend(
        [
            "## Totals",
            "",
            f"- Passed: {summary.totals['passed']}",
            f"- Failed: {summary.totals['failed']}",
            f"- Skipped: {summary.totals['skipped']}",
            f"- Warning: {summary.totals['warning']}",
            "",
            "## Checks",
            "",
        ]
    )

    if not summary.checks:
        lines.append("- No checks were executed.")
    else:
        for check in summary.checks:
            detail = (
                f"- {check.id}: {check.status} ({check.tool}, exit {check.exit_code})"
            )
            if check.message:
                detail += f" - {check.message}"
            lines.append(detail)

    return "\n".join(lines).strip() + "\n"


def format_list(items: list[str]) -> str:
    """Render a compact list for Markdown summaries."""
    return ", ".join(items) if items else "none"
