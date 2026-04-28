"""Backlog-reseeding candidate input helpers for self-improvement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.improvement_state import backlog_file, open_backlog_items

__all__ = [
    "discover_backlog_reseeding_candidate_inputs",
]

RESEEDING_SUPPORTING_CATEGORIES = {
    "coverage_gap",
    "docs_drift",
    "schema_drift",
    "workflow_gap",
    "integration_gap",
    "worktree_risk",
    "commit_isolation_gap",
    "artifact_hygiene_gap",
    "runtime_artifact_cleanup_gap",
    "deferred_cleanup_gap",
    "evidence_freshness_gap",
    "autonomy_selection_gap",
}


def discover_backlog_reseeding_candidate_inputs(
    root: Path,
    *,
    backlog: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return a reseeding candidate when open backlog work would otherwise vanish."""
    if open_backlog_items(backlog):
        return []
    supporting = [
        candidate
        for candidate in candidates
        if str(candidate.get("category") or "") in RESEEDING_SUPPORTING_CATEGORIES
    ]
    if not supporting:
        return []
    evidence = [
        {
            "source": "backlog",
            "path": backlog_file(root),
            "summary": "no open backlog items were available before reseeding",
        }
    ]
    for candidate in supporting[:2]:
        first_evidence = next(
            (item for item in candidate.get("evidence", []) if isinstance(item, dict)),
            None,
        )
        if first_evidence is not None:
            evidence.append(dict(first_evidence))
    return [
        {
            "id": "backlog_reseeding_gap-empty-open-backlog",
            "title": "Reseed the self-improvement backlog from structural evidence",
            "category": "backlog_reseeding_gap",
            "evidence": evidence,
            "impact": 3,
            "likelihood": 3,
            "confidence": 4,
            "repair_cost": 3,
            "recommendation": "improve_backlog_reseeding",
            "signals": ["roadmap_gap"],
        }
    ]
