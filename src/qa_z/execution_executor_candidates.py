"""Executor-result and ingest candidate helpers for execution discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.backlog_core import BacklogCandidate, slugify, unique_candidates
from qa_z.executor_signals import (
    discover_executor_ingest_candidate_inputs,
    discover_executor_result_candidate_inputs,
)

__all__ = [
    "discover_executor_ingest_candidates",
    "discover_executor_result_candidates",
]


def discover_executor_result_candidates(root: Path) -> list[Any]:
    """Create candidates from stored executor-result artifacts."""
    candidates: list[Any] = []
    for candidate_input in discover_executor_result_candidate_inputs(root):
        candidates.append(
            BacklogCandidate(
                id=(
                    f"executor_result_gap-{slugify(str(candidate_input['session_id']))}"
                ),
                title=str(candidate_input["title"]),
                category="executor_result_gap",
                evidence=[
                    {
                        "source": "executor_result",
                        "path": format_path(candidate_input["path"], root),
                        "summary": (
                            f"status={candidate_input['result_status']}; "
                            f"validation={candidate_input['validation_status'] or 'unknown'}; "
                            f"hint={candidate_input['verification_hint']}"
                        ),
                    }
                ],
                impact=int(candidate_input["impact"]),
                likelihood=4,
                confidence=int(candidate_input["confidence"]),
                repair_cost=3,
                recommendation=str(candidate_input["recommendation"]),
                signals=list(candidate_input["signals"]),
            )
        )
    return unique_candidates(candidates)


def discover_executor_ingest_candidates(root: Path) -> list[Any]:
    """Create candidates from stored executor ingest outcomes and implications."""
    candidates: list[Any] = []
    for candidate_input in discover_executor_ingest_candidate_inputs(root):
        candidates.append(
            BacklogCandidate(
                id=str(candidate_input["id"]),
                title=str(candidate_input["title"]),
                category=str(candidate_input["category"]),
                evidence=[
                    {
                        "source": "executor_result_ingest",
                        "path": format_path(candidate_input["path"], root),
                        "summary": str(candidate_input["summary"]),
                    }
                ],
                impact=int(candidate_input["impact"]),
                likelihood=int(candidate_input["likelihood"]),
                confidence=int(candidate_input["confidence"]),
                repair_cost=int(candidate_input["repair_cost"]),
                recommendation=str(candidate_input["recommendation"]),
                signals=list(candidate_input["signals"]),
            )
        )
    return unique_candidates(candidates)
