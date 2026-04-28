"""Thin public wrappers for GitHub summary render seams."""

from __future__ import annotations

from pathlib import Path

from qa_z.artifacts import RunSource
from qa_z.reporters.verification_publish import (
    SessionPublishSummary,
    VerificationPublishSummary,
)
from qa_z.runners.models import RunSummary


def render_github_summary(
    *,
    summary: RunSummary,
    run_source: RunSource,
    root: Path,
    deep_summary: RunSummary | None = None,
    publish_summary: VerificationPublishSummary | SessionPublishSummary | None = None,
) -> str:
    """Render a compact QA-Z run summary for GitHub Actions."""
    from qa_z.reporters import github_summary as github_summary_module

    return github_summary_module._render_github_summary_impl(
        summary=summary,
        run_source=run_source,
        root=root,
        deep_summary=deep_summary,
        publish_summary=publish_summary,
    )
