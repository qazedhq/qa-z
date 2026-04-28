"""Verification artifact load/write helpers."""

from __future__ import annotations

from qa_z.verification_artifact_loading import load_verification_run
from qa_z.verification_artifact_writing import write_verification_artifacts
from qa_z.verification_models import VerificationComparison
from qa_z.verification_report import render_verification_report_impl

__all__ = [
    "load_verification_run",
    "render_verification_report",
    "write_verification_artifacts",
]


def render_verification_report(comparison: VerificationComparison) -> str:
    """Render the human-readable Markdown verification report."""
    return render_verification_report_impl(comparison)
