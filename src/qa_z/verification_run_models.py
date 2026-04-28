"""Run and comparison verification models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from qa_z.runners.models import RunSummary
from qa_z.verification_delta_models import (
    FastCheckDelta,
    VerificationCategory,
    VerificationFindingDelta,
)

VerificationVerdict = Literal[
    "improved",
    "unchanged",
    "mixed",
    "regressed",
    "verification_failed",
]


@dataclass(frozen=True)
class VerificationRun:
    """Loaded evidence for one baseline or candidate run."""

    run_id: str
    run_dir: str
    fast_summary: RunSummary
    deep_summary: RunSummary | None = None


@dataclass(frozen=True)
class VerificationComparison:
    """Full comparison result for a baseline and candidate run."""

    baseline: VerificationRun
    candidate: VerificationRun
    verdict: VerificationVerdict
    fast_checks: dict[VerificationCategory, list[FastCheckDelta]]
    deep_findings: dict[VerificationCategory, list[VerificationFindingDelta]]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        """Render the comparison as deterministic JSON-safe data."""
        return {
            "kind": "qa_z.verify_compare",
            "schema_version": 1,
            "baseline_run_id": self.baseline.run_id,
            "candidate_run_id": self.candidate.run_id,
            "baseline": {
                "run_dir": self.baseline.run_dir,
                "fast_status": self.baseline.fast_summary.status,
                "deep_status": (
                    self.baseline.deep_summary.status
                    if self.baseline.deep_summary is not None
                    else None
                ),
            },
            "candidate": {
                "run_dir": self.candidate.run_dir,
                "fast_status": self.candidate.fast_summary.status,
                "deep_status": (
                    self.candidate.deep_summary.status
                    if self.candidate.deep_summary is not None
                    else None
                ),
            },
            "verdict": self.verdict,
            "fast_checks": {
                category: [delta.to_dict() for delta in deltas]
                for category, deltas in self.fast_checks.items()
            },
            "deep_findings": {
                category: [delta.to_dict() for delta in deltas]
                for category, deltas in self.deep_findings.items()
            },
            "summary": dict(self.summary),
        }


@dataclass(frozen=True)
class VerificationArtifactPaths:
    """Paths written for a verification comparison."""

    summary_path: Path
    compare_path: Path
    report_path: Path


__all__ = [
    "VerificationArtifactPaths",
    "VerificationComparison",
    "VerificationRun",
    "VerificationVerdict",
]
