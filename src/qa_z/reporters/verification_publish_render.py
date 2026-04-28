"""Thin public wrappers for verification-publish render seams."""

from __future__ import annotations

from qa_z.reporters.verification_publish_models import (
    SessionPublishSummary,
    VerificationPublishSummary,
)


def render_publish_summary_markdown(
    summary: VerificationPublishSummary | SessionPublishSummary,
) -> str:
    """Render concise Markdown suitable for a GitHub Actions Job Summary."""
    from qa_z.reporters import verification_publish as verification_publish_module

    return verification_publish_module._render_publish_summary_markdown_impl(summary)


def publish_headline(
    *,
    verdict: str,
    resolved_count: int,
    remaining_count: int,
    regression_count: int,
) -> str:
    """Return a short outcome headline."""
    from qa_z.reporters import verification_publish as verification_publish_module

    return verification_publish_module._publish_headline_impl(
        verdict=verdict,
        resolved_count=resolved_count,
        remaining_count=remaining_count,
        regression_count=regression_count,
    )
