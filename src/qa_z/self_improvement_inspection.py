"""Self-inspection workflow helpers for self-improvement."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qa_z.backlog_core import (
    BacklogCandidate,
    evidence_sources,
    merge_backlog,
    unique_candidates,
)
from qa_z.discovery_pipeline import run_discovery_pipeline
from qa_z.improvement_state import backlog_file, empty_backlog, load_backlog
from qa_z.improvement_state import open_backlog_items
from qa_z.self_improvement_constants import (
    BACKLOG_KIND,
    SELF_IMPROVEMENT_SCHEMA_VERSION,
    SELF_INSPECTION_KIND,
)
from qa_z.self_improvement_registry import DISCOVERY_PIPELINE_STAGES
from qa_z.self_improvement_runtime import default_loop_id, utc_now, write_json

__all__ = [
    "SelfInspectionArtifactPaths",
    "discover_candidates",
    "run_self_inspection",
]


def _surface():
    import qa_z.self_improvement as si

    return si


@dataclass(frozen=True)
class SelfInspectionArtifactPaths:
    """Paths written by a self-inspection pass."""

    self_inspection_path: Path
    backlog_path: Path


def run_self_inspection(
    *, root: Path, now: str | None = None, loop_id: str | None = None
) -> SelfInspectionArtifactPaths:
    """Inspect local QA-Z artifacts and update the improvement backlog."""
    si = _surface()
    root = root.resolve()
    generated_at = now or utc_now()
    resolved_loop_id = loop_id or default_loop_id("inspect", generated_at)
    existing_backlog = load_backlog(root)
    live_signals = si.collect_live_repository_signals(root)
    candidates = discover_candidates(
        root,
        existing=existing_backlog,
        live_signals=live_signals,
        generated_at=generated_at,
    )
    reseeded_candidate_ids = _reseeded_candidate_ids(existing_backlog, candidates)
    report = {
        "kind": SELF_INSPECTION_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "loop_id": resolved_loop_id,
        "generated_at": generated_at,
        "backlog_reseeded": bool(reseeded_candidate_ids),
        "reseeded_candidate_ids": reseeded_candidate_ids,
        "live_repository": si.live_repository_summary(live_signals),
        "evidence_sources": evidence_sources(candidates),
        "candidates": [candidate.to_dict() for candidate in candidates],
    }
    backlog = merge_backlog(
        existing=existing_backlog,
        candidates=candidates,
        now=generated_at,
        schema_version=SELF_IMPROVEMENT_SCHEMA_VERSION,
        backlog_kind=BACKLOG_KIND,
        root=root,
        live_signals=live_signals,
    )

    latest_dir = root / ".qa-z" / "loops" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    self_inspection_path = latest_dir / "self_inspect.json"
    backlog_path = backlog_file(root)
    write_json(self_inspection_path, report)
    write_json(backlog_path, backlog)
    return SelfInspectionArtifactPaths(
        self_inspection_path=self_inspection_path,
        backlog_path=backlog_path,
    )


def _reseeded_candidate_ids(
    existing_backlog: dict[str, Any], candidates: list[BacklogCandidate]
) -> list[str]:
    """Return concrete candidate ids when inspection had to reseed an empty backlog."""
    if open_backlog_items(existing_backlog):
        return []
    return [
        candidate.id
        for candidate in candidates
        if candidate.category != "backlog_reseeding_gap"
    ]


def discover_candidates(
    root: Path,
    existing: dict[str, Any] | None = None,
    live_signals: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> list[BacklogCandidate]:
    """Find evidence-backed improvement candidates in local artifacts."""
    si = _surface()
    backlog = existing or empty_backlog()
    live_signals = live_signals or si.collect_live_repository_signals(root)
    candidates = run_discovery_pipeline(
        root=root,
        backlog=backlog,
        live_signals=live_signals,
        generated_at=generated_at,
        stages=DISCOVERY_PIPELINE_STAGES,
    )
    return unique_candidates(sorted(candidates, key=lambda candidate: candidate.id))
