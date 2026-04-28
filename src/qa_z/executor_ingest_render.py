"""Render helpers for executor-result ingest summaries and reports."""

from __future__ import annotations

from typing import Any

from qa_z.executor_ingest_render_support import (
    ingest_check_stdout_line,
    ingest_implication_stdout_summary,
    ingest_text_field,
    ingest_warning_stdout_summary,
)
from qa_z.live_repository import render_live_repository_summary


def render_executor_result_ingest_stdout(summary: dict[str, Any]) -> str:
    """Render a concise operator-facing ingest status summary."""
    lines = [
        f"qa-z executor-result ingest: {summary.get('ingest_status', summary['result_status'])}",
        f"Result: {summary['result_status']}",
        f"Session: {summary['session_id']}",
        f"Stored result: {summary.get('stored_result_path') or 'none'}",
        f"Ingest report: {summary.get('ingest_report_path') or 'none'}",
        f"Verify resume: {summary.get('verify_resume_status', 'verify_blocked')}",
        f"Verification: {summary['verification_verdict'] or 'not_run'}",
    ]
    source_self_inspection = ingest_text_field(
        summary.get("source_self_inspection"), "unknown"
    )
    source_loop = ingest_text_field(
        summary.get("source_self_inspection_loop_id"), "unknown"
    )
    source_generated_at = ingest_text_field(
        summary.get("source_self_inspection_generated_at"), "unknown"
    )
    if any(
        value != "unknown"
        for value in (source_self_inspection, source_loop, source_generated_at)
    ):
        lines.append(f"Source self-inspection: {source_self_inspection}")
        lines.append(f"Source loop: {source_loop}")
        lines.append(f"Source generated at: {source_generated_at}")
    live_repository = summary.get("live_repository")
    if isinstance(live_repository, dict):
        lines.append(
            f"Live repository: {render_live_repository_summary(live_repository)}"
        )
    lines.append(ingest_check_stdout_line("Freshness", summary.get("freshness_check")))
    lines.append(
        ingest_check_stdout_line("Provenance", summary.get("provenance_check"))
    )
    warning_summary = ingest_warning_stdout_summary(summary.get("warnings"))
    if warning_summary:
        lines.append(f"Warnings: {warning_summary}")
    implication_summary = ingest_implication_stdout_summary(
        summary.get("backlog_implications")
    )
    if implication_summary:
        lines.append(f"Backlog implications: {implication_summary}")
    lines.append(f"Next: {summary['next_recommendation']}")
    return "\n".join(lines)


def render_ingest_report(summary: dict[str, Any]) -> str:
    """Render a human-readable executor-result ingest report."""
    lines = [
        "# QA-Z Executor Result Ingest Report",
        "",
        f"- Result id: `{summary.get('result_id')}`",
        f"- Ingest status: `{summary.get('ingest_status')}`",
        f"- Result status: `{summary.get('result_status')}`",
        f"- Bridge: `{summary.get('bridge_id')}`",
        f"- Session: `{summary.get('session_id')}`",
        f"- Verify resume: `{summary.get('verify_resume_status')}`",
        f"- Verification: `{summary.get('verification_verdict') or 'not_run'}`",
        f"- Next: {summary.get('next_recommendation')}",
    ]
    live_repository = summary.get("live_repository")
    source_context_present = any(
        str(summary.get(key) or "").strip()
        for key in (
            "source_self_inspection",
            "source_self_inspection_loop_id",
            "source_self_inspection_generated_at",
        )
    )
    if source_context_present:
        source_self_inspection = ingest_text_field(
            summary.get("source_self_inspection"), "unknown"
        )
        source_loop = ingest_text_field(
            summary.get("source_self_inspection_loop_id"), "unknown"
        )
        source_generated_at = ingest_text_field(
            summary.get("source_self_inspection_generated_at"), "unknown"
        )
        lines.extend(
            [
                "",
                "## Source Context",
                "",
                f"- Source self-inspection: `{source_self_inspection}`",
                f"- Source loop: `{source_loop}`",
                f"- Source generated at: `{source_generated_at}`",
            ]
        )
    if isinstance(live_repository, dict):
        lines.extend(
            [
                "",
                "## Live Repository Context",
                "",
                f"- {render_live_repository_summary(live_repository)}",
            ]
        )
    lines.extend(["", "## Warnings", ""])
    warnings = summary.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(f"- `{warning}`" for warning in warnings)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Freshness",
            "",
            f"- Status: `{summary.get('freshness_check', {}).get('status', 'unknown')}`",
        ]
    )
    lines.extend(
        f"- {detail}"
        for detail in summary.get("freshness_check", {}).get("details", [])
        if str(detail).strip()
    )
    lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- Status: `{summary.get('provenance_check', {}).get('status', 'unknown')}`",
        ]
    )
    lines.extend(
        f"- {detail}"
        for detail in summary.get("provenance_check", {}).get("details", [])
        if str(detail).strip()
    )
    lines.extend(["", "## Backlog Implications", ""])
    implications = summary.get("backlog_implications")
    if isinstance(implications, list) and implications:
        for item in implications:
            if not isinstance(item, dict):
                continue
            lines.append(
                f"- `{item.get('category', 'workflow_gap')}`: {item.get('summary', '')}"
            )
    else:
        lines.append("- none")
    return "\n".join(lines).strip() + "\n"
