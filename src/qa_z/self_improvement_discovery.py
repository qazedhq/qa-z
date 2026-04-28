"""Discovery wrappers that adapt normalized signals into backlog candidates."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.backlog_reseeding_signals import (
    discover_backlog_reseeding_candidate_inputs,
)
from qa_z.backlog_core import (
    BacklogCandidate,
    candidate_from_input,
    slugify,
    unique_candidates,
)
from qa_z.benchmark_signals import discover_benchmark_candidate_inputs
from qa_z.loop_history_candidates import (
    discover_empty_loop_candidate_inputs,
    discover_repeated_fallback_family_candidate_inputs,
)

__all__ = [
    "benchmark_candidate",
    "discover_backlog_reseeding_candidates",
    "discover_benchmark_candidates",
    "discover_empty_loop_candidates",
    "discover_repeated_fallback_family_candidates",
]


def discover_benchmark_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from failed benchmark summary artifacts."""
    candidates: list[BacklogCandidate] = []
    for candidate_input in discover_benchmark_candidate_inputs(root):
        candidates.append(
            benchmark_candidate(
                root,
                candidate_input["path"],
                str(candidate_input["fixture_name"]),
                failures=list(candidate_input["failures"]),
                snapshot=str(candidate_input.get("snapshot") or ""),
            )
        )
    return unique_candidates(candidates)


def benchmark_candidate(
    root: Path,
    path: Path,
    fixture_name: str,
    *,
    failures: list[str],
    snapshot: str = "",
) -> BacklogCandidate:
    """Build a benchmark-gap candidate from one failed fixture."""
    name = fixture_name or "unknown"
    summary = (
        f"fixture={name}; failures={'; '.join(failures[:3])}"
        if failures
        else f"fixture={name} failed"
    )
    if snapshot:
        summary = f"snapshot={snapshot}; {summary}"
    return BacklogCandidate(
        id=f"benchmark_gap-{slugify(name)}",
        title=f"Fix benchmark fixture failure: {name}",
        category="benchmark_gap",
        evidence=[
            {
                "source": "benchmark",
                "path": format_path(path, root),
                "summary": summary,
            }
        ],
        impact=4,
        likelihood=4,
        confidence=4,
        repair_cost=4,
        recommendation="add_benchmark_fixture",
        signals=["benchmark_fail"],
    )


def discover_empty_loop_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from repeated empty-loop history chains."""
    return [
        candidate_from_input(root, candidate_input)
        for candidate_input in discover_empty_loop_candidate_inputs(root)
    ]


def discover_repeated_fallback_family_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from repeated fallback-family reuse in recent loops."""
    return [
        candidate_from_input(root, candidate_input)
        for candidate_input in discover_repeated_fallback_family_candidate_inputs(root)
    ]


def discover_backlog_reseeding_candidates(
    root: Path, backlog: dict[str, Any], candidates: list[BacklogCandidate]
) -> list[BacklogCandidate]:
    """Create a backlog-reseeding candidate when open work would otherwise vanish."""
    candidate_inputs = discover_backlog_reseeding_candidate_inputs(
        root,
        backlog=backlog,
        candidates=[candidate.to_dict() for candidate in candidates],
    )
    return [
        candidate_from_input(root, candidate_input)
        for candidate_input in candidate_inputs
    ]
