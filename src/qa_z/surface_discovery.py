"""Artifact-surface and coverage discovery surface for self-improvement."""

from __future__ import annotations

from qa_z.artifact_consistency_discovery import (
    discover_artifact_consistency_candidates,
)
from qa_z.coverage_gap_discovery import discover_coverage_gap_candidates
from qa_z.docs_surface_discovery import discover_docs_drift_candidates

__all__ = [
    "discover_artifact_consistency_candidates",
    "discover_coverage_gap_candidates",
    "discover_docs_drift_candidates",
]
