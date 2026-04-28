"""Ordered discovery pipeline helpers for candidate collection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from qa_z.backlog_core import BacklogCandidate

__all__ = ["DiscoveryStage", "run_discovery_pipeline"]


@dataclass(frozen=True)
class DiscoveryStage:
    """One ordered discovery stage in the self-improvement pipeline."""

    name: str
    run: Callable[
        [Path, dict[str, Any], list[BacklogCandidate], dict[str, Any], str | None],
        list[BacklogCandidate],
    ]


def run_discovery_pipeline(
    *,
    root: Path,
    backlog: dict[str, Any],
    live_signals: dict[str, Any],
    generated_at: str | None,
    stages: list[DiscoveryStage],
) -> list[BacklogCandidate]:
    """Run an ordered discovery pipeline while exposing accumulated candidates."""
    candidates: list[BacklogCandidate] = []
    for stage in stages:
        stage_candidates = stage.run(
            root, backlog, list(candidates), live_signals, generated_at
        )
        candidates.extend(stage_candidates)
    return candidates
