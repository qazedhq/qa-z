"""Thin public wrappers for run-summary artifact seams."""

from __future__ import annotations

from pathlib import Path

from qa_z.runners.models import RunSummary


def write_run_summary_artifacts(summary: RunSummary, artifact_dir: Path) -> Path:
    """Write summary JSON, Markdown, and per-check JSON artifacts."""
    from qa_z.reporters import run_summary as run_summary_module

    return run_summary_module._write_run_summary_artifacts_impl(summary, artifact_dir)
