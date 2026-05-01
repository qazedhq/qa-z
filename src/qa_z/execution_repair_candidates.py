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
        run_id = str(candidate_input["run_id"])
        verdict = str(candidate_input["verdict"])
        candidate_id, title, category = verification_candidate_identity(
            verdict=verdict,
            run_id=run_id,
        )
        candidates.append(
            BacklogCandidate(
                id=candidate_id,
                title=title,
                category=category,
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


def verification_candidate_identity(
    *, verdict: str, run_id: str
) -> tuple[str, str, str]:
    """Return id, title, and category for one verification candidate."""
    run_slug = slugify(run_id)
    if verdict == "verification_failed":
        return (
            f"verify_failure-{run_slug}",
            f"Stabilize failed verification artifacts: {run_id}",
            "verification_failure",
        )
    return (
        f"verify_regression-{run_slug}",
        f"Stabilize verification verdict: {verdict} in {run_id}",
        "verify_regression",
    )


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
