"""Artifact-consistency discovery helpers for self-improvement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.backlog_core import BacklogCandidate, slugify

__all__ = [
    "discover_artifact_consistency_candidates",
]


def discover_artifact_consistency_candidates(root: Path) -> list[Any]:
    """Create candidates when related local artifacts are missing."""
    candidates: list[Any] = []
    qa_root = root / ".qa-z"
    if not qa_root.exists():
        return candidates
    for summary_path in sorted(qa_root.rglob("verify/summary.json")):
        missing = [
            sibling.name
            for sibling in (
                summary_path.parent / "compare.json",
                summary_path.parent / "report.md",
            )
            if not sibling.is_file()
        ]
        if not missing:
            continue
        candidates.append(
            BacklogCandidate(
                id=f"artifact_consistency-{slugify(summary_path.parent.parent.name)}",
                title=(
                    "Restore verification companion artifacts for "
                    f"{summary_path.parent.parent.name}"
                ),
                category="artifact_consistency",
                evidence=[
                    {
                        "source": "verification",
                        "path": format_path(summary_path, root),
                        "summary": "missing companions: " + ", ".join(missing),
                    }
                ],
                impact=3,
                likelihood=3,
                confidence=4,
                repair_cost=2,
                recommendation="sync_contract_and_docs",
                signals=[],
            )
        )
    return candidates
