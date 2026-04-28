"""Thin public wrappers for verification-publish loading seams."""

from __future__ import annotations

from pathlib import Path

from qa_z.artifacts import RunSource
from qa_z.reporters.verification_publish_models import (
    SessionPublishSummary,
    VerificationPublishSummary,
)


def detect_publish_summary_for_run(
    *, root: Path, run_source: RunSource
) -> VerificationPublishSummary | SessionPublishSummary | None:
    """Find a publishable repair outcome related to a run, if one exists."""
    from qa_z.reporters import verification_publish as verification_publish_module

    return verification_publish_module._detect_publish_summary_for_run_impl(
        root=root,
        run_source=run_source,
    )


def build_verification_publish_summary(
    *, root: Path, verify_dir: Path
) -> VerificationPublishSummary:
    """Build a concise publish summary from verification artifacts."""
    from qa_z.reporters import verification_publish as verification_publish_module

    return verification_publish_module._build_verification_publish_summary_impl(
        root=root,
        verify_dir=verify_dir,
    )


def load_session_publish_summary(
    *, root: Path, session: str | Path
) -> SessionPublishSummary:
    """Build a concise publish summary from a repair-session directory."""
    from qa_z.reporters import verification_publish as verification_publish_module

    return verification_publish_module._load_session_publish_summary_impl(
        root=root,
        session=session,
    )
