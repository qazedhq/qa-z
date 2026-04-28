"""Thin public wrappers for run-summary render seams."""

from __future__ import annotations

from qa_z.runners.models import RunSummary


def render_summary_markdown(summary: RunSummary) -> str:
    """Render a compact human-readable run summary."""
    from qa_z.reporters import run_summary as run_summary_module

    return run_summary_module._render_summary_markdown_impl(summary)
