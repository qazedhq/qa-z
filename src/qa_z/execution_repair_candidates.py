"""Repair-oriented execution candidate helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.backlog_core import BacklogCandidate, slugify, unique_candidates
from qa_z.repair_signals import (
    discover_session_candidate_inputs,
    discover_verification_candidate_inputs,
)

__all__ = [
    "discover_session_candidates",
    "discover_verification_candidates",
]


def discover_verification_candidates(root: Path) -> list[Any]:
    """Create candidates from problematic verification verdicts."""
    candidates: list[Any] = []
    for candidate_input in discover_verification_candidate_inputs(root):
        candidates.append(
            BacklogCandidate(
                id=f"verify_regression-{slugify(str(candidate_input['run_id']))}",
                title=(
                    "Stabilize verification verdict: "
                    f"{candidate_input['verdict']} in {candidate_input['run_id']}"
                ),
                category="verify_regression",
                evidence=[
                    {
                        "source": "verification",
                        "path": format_path(candidate_input["path"], root),
                        "summary": str(candidate_input["summary"]),
                    }
                ],
                impact=int(candidate_input["impact"]),
                likelihood=4,
                confidence=4,
                repair_cost=4,
                recommendation="stabilize_verification_surface",
                signals=list(candidate_input["signals"]),
            )
        )
    return unique_candidates(candidates)


def discover_session_candidates(root: Path) -> list[Any]:
    """Create candidates from incomplete repair sessions."""
    candidates: list[Any] = []
    for candidate_input in discover_session_candidate_inputs(root):
        candidates.append(
            BacklogCandidate(
                id=f"session_gap-{slugify(str(candidate_input['session_id']))}",
                title=(
                    "Resolve incomplete repair session: "
                    f"{candidate_input['session_id']}"
                ),
                category="session_gap",
                evidence=[
                    {
                        "source": "repair_session",
                        "path": format_path(candidate_input["path"], root),
                        "summary": f"state={candidate_input['state']}",
                    }
                ],
                impact=3,
                likelihood=4,
                confidence=4,
                repair_cost=3,
                recommendation="create_repair_session",
                signals=[],
            )
        )
    return unique_candidates(candidates)
