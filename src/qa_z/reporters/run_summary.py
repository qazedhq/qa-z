"""Reporters for deterministic runner summaries."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.reporters.run_summary_artifacts import write_run_summary_artifacts
from qa_z.reporters.run_summary_render import render_summary_markdown
from qa_z.runners.models import RunSummary

__all__ = [
    "format_bool",
    "format_list",
    "nonnegative_int",
    "render_diagnostics_markdown",
    "render_summary_markdown",
    "string_list",
    "write_run_summary_artifacts",
]


def _write_run_summary_artifacts_impl(summary: RunSummary, artifact_dir: Path) -> Path:
    """Write summary JSON, Markdown, and per-check JSON artifacts."""
    artifact_dir.mkdir(parents=True, exist_ok=True)
    checks_dir = artifact_dir / "checks"
    checks_dir.mkdir(parents=True, exist_ok=True)

    summary_path = artifact_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (artifact_dir / "summary.md").write_text(
        _render_summary_markdown_impl(summary), encoding="utf-8"
    )

    for check in summary.checks:
        check_path = checks_dir / f"{check.id}.json"
        check_path.write_text(
            json.dumps(check.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    return summary_path


def _render_summary_markdown_impl(summary: RunSummary) -> str:
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
    if summary.run_resolution:
        fast_summary_path = summary.run_resolution.get("fast_summary_path")
        lines.extend(
            [
                "## Run Resolution",
                "",
                f"- Source: {summary.run_resolution.get('source') or 'unknown'}",
                "- Attached to fast run: "
                f"{format_bool(summary.run_resolution.get('attached_to_fast_run'))}",
                f"- Run dir: {summary.run_resolution.get('run_dir') or 'unknown'}",
                f"- Deep dir: {summary.run_resolution.get('deep_dir') or 'unknown'}",
                f"- Fast summary: {fast_summary_path or 'none'}",
                "",
            ]
        )
    if summary.diagnostics:
        lines.extend(render_diagnostics_markdown(summary.diagnostics))
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


def render_diagnostics_markdown(diagnostics: dict[str, object]) -> list[str]:
    """Render optional runner diagnostics into the human-readable summary."""
    lines = ["## Diagnostics", ""]
    scan_quality = diagnostics.get("scan_quality")
    if isinstance(scan_quality, dict):
        status = scan_quality.get("status") or "unknown"
        warning_count = nonnegative_int(scan_quality.get("warning_count"))
        warning_noun = "warning" if warning_count == 1 else "warnings"
        warning_types = string_list(scan_quality.get("warning_types"))
        warning_paths = string_list(scan_quality.get("warning_paths"))
        check_ids = string_list(scan_quality.get("check_ids"))
        lines.extend(
            [
                f"- Scan quality: {status} ({warning_count} {warning_noun})",
                f"- Warning types: {format_list(warning_types)}",
                f"- Warning paths: {format_list(warning_paths)}",
                f"- Warning checks: {format_list(check_ids)}",
                "",
            ]
        )
    else:
        lines.extend(["- none", ""])
    return lines


def string_list(value: object) -> list[str]:
    """Return a list of non-empty strings for optional diagnostics fields."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def nonnegative_int(value: object) -> int:
    """Return a non-negative integer or 0 for malformed diagnostics values."""
    if not isinstance(value, (int, float, str)):
        return 0
    try:
        number = int(value)
    except ValueError:
        return 0
    return max(number, 0)


def format_list(items: list[str]) -> str:
    """Render a compact list for Markdown summaries."""
    return ", ".join(items) if items else "none"


def format_bool(value: object) -> str:
    """Render JSON-like booleans for Markdown summaries."""
    return "yes" if value is True else "no"
