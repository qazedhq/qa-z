"""Backlog candidate modeling and merge helpers for self-improvement."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.live_repository import (
    has_cleanup_artifact_pressure,
    has_commit_isolation_worktree_pressure,
    has_live_worktree_changes,
    has_non_current_truth_worktree_pressure,
)

__all__ = [
    "BacklogCandidate",
    "candidate_from_input",
    "evidence_sources",
    "format_report_evidence",
    "int_value",
    "merge_backlog",
    "score_candidate",
    "slugify",
    "unique_candidates",
]

OPEN_STATUSES = {"open", "selected", "in_progress"}
NON_PERSISTED_SYNTHETIC_CATEGORIES = {"backlog_reseeding_gap"}


@dataclass(frozen=True)
class BacklogCandidate:
    """Evidence-backed improvement candidate before backlog merge."""

    id: str
    title: str
    category: str
    evidence: list[dict[str, Any]]
    impact: int
    likelihood: int
    confidence: int
    repair_cost: int
    recommendation: str
    signals: list[str]
    recurrence_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Render the candidate as JSON-safe data."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "evidence": list(self.evidence),
            "impact": self.impact,
            "likelihood": self.likelihood,
            "confidence": self.confidence,
            "repair_cost": self.repair_cost,
            "priority_score": score_candidate(self),
            "recommendation": self.recommendation,
            "signals": list(self.signals),
            "recurrence_count": self.recurrence_count,
        }


def score_candidate(candidate: BacklogCandidate) -> int:
    """Score one candidate using deterministic impact and evidence bonuses."""
    score = (
        candidate.impact * candidate.likelihood * candidate.confidence
    ) - candidate.repair_cost
    signals = set(candidate.signals)
    if "benchmark_fail" in signals:
        score += 2
    if {"verify_regressed", "verify_mixed"} & signals:
        score += 2
    if "schema_doc_drift" in signals:
        score += 1
    if "executor_validation_failed" in signals:
        score += 2
    if "executor_result_no_op" in signals:
        score += 1
    if "executor_result_failed" in signals:
        score += 1
    if "executor_dry_run_blocked" in signals:
        score += 2
    if "executor_dry_run_attention" in signals:
        score += 1
    if "mixed_surface_realism_gap" in signals:
        score += 2
    if "recent_empty_loop_chain" in signals:
        score += 2
    if "recent_fallback_family_repeat" in signals:
        score += 2
    if "worktree_integration_risk" in signals:
        score += 1
    if "dirty_worktree_large" in signals:
        score += 2
    if "commit_order_dependency_exists" in signals:
        score += 2
    if "deferred_cleanup_repeated" in signals:
        score += 1
    if "generated_artifact_policy_ambiguity" in signals:
        score += 1
    if "policy_managed_runtime_artifacts" in signals:
        score += 2
    if "service_readiness_gap" in signals:
        score += 2
    if "roadmap_gap" in signals:
        score += 2
    if candidate.recurrence_count >= 2:
        score += 1
    if "regression_prevention" in signals:
        score += 1
    return int(score)


def merge_backlog(
    *,
    existing: dict[str, Any],
    candidates: list[BacklogCandidate],
    now: str,
    schema_version: int,
    backlog_kind: str,
    root: Path | None = None,
    live_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge newly observed candidates into a persistent backlog artifact."""
    candidates = _persisted_backlog_candidates(candidates)
    existing_items = [
        item for item in existing.get("items", []) if isinstance(item, dict)
    ]
    items_by_id = {str(item.get("id")): dict(item) for item in existing_items}
    observed_ids = {candidate.id for candidate in candidates}

    for candidate in candidates:
        previous = items_by_id.get(candidate.id)
        recurrence = int_value(previous.get("recurrence_count")) + 1 if previous else 1
        seen_candidate = replace(candidate, recurrence_count=recurrence)
        item = seen_candidate.to_dict()
        item.update(
            {
                "status": "open",
                "first_seen_at": (
                    str(previous.get("first_seen_at"))
                    if previous and previous.get("first_seen_at")
                    else now
                ),
                "last_seen_at": now,
            }
        )
        items_by_id[candidate.id] = item

    for item_id, item in items_by_id.items():
        if item_id in observed_ids:
            continue
        if str(item.get("status", "open")) != "open":
            continue
        item["status"] = "closed"
        item["closed_at"] = now
        item["closure_reason"] = _unobserved_backlog_closure_reason(
            item,
            root=root,
            live_signals=live_signals,
            generated_at=now,
        )

    items = sorted(
        items_by_id.values(),
        key=lambda item: (
            0 if str(item.get("status", "open")) in OPEN_STATUSES else 1,
            -int_value(item.get("priority_score")),
            str(item.get("id", "")),
        ),
    )
    return {
        "kind": backlog_kind,
        "schema_version": schema_version,
        "updated_at": now,
        "items": items,
    }


def _persisted_backlog_candidates(
    candidates: list[BacklogCandidate],
) -> list[BacklogCandidate]:
    """Keep persisted backlog items focused on concrete follow-up work."""
    concrete_candidates = [
        candidate
        for candidate in candidates
        if candidate.category not in NON_PERSISTED_SYNTHETIC_CATEGORIES
    ]
    if concrete_candidates:
        return concrete_candidates
    return candidates


def evidence_sources(candidates: list[BacklogCandidate]) -> list[dict[str, str]]:
    """Return unique artifact sources used by candidates."""
    sources: dict[tuple[str, str], dict[str, str]] = {}
    for candidate in candidates:
        for entry in candidate.evidence:
            source = str(entry.get("source") or "artifact")
            path = str(entry.get("path") or "")
            if not path:
                continue
            sources[(source, path)] = {"source": source, "path": path}
    return [sources[key] for key in sorted(sources)]


def candidate_from_input(
    root: Path, candidate_input: dict[str, Any]
) -> BacklogCandidate:
    """Build a backlog candidate from a normalized candidate-input packet."""
    evidence: list[dict[str, str]] = []
    for item in candidate_input.get("evidence", []):
        if not isinstance(item, dict):
            continue
        raw_path = item.get("path")
        evidence.append(
            {
                "source": str(item.get("source") or "artifact"),
                "path": (
                    format_path(raw_path, root)
                    if isinstance(raw_path, Path)
                    else str(raw_path or "")
                ),
                "summary": str(item.get("summary") or ""),
            }
        )
    return BacklogCandidate(
        id=str(candidate_input["id"]),
        title=str(candidate_input["title"]),
        category=str(candidate_input["category"]),
        evidence=evidence,
        impact=int(candidate_input["impact"]),
        likelihood=int(candidate_input["likelihood"]),
        confidence=int(candidate_input["confidence"]),
        repair_cost=int(candidate_input["repair_cost"]),
        recommendation=str(candidate_input["recommendation"]),
        signals=list(candidate_input["signals"]),
    )


def format_report_evidence(
    root: Path, evidence: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Normalize report evidence paths into JSON-safe repository-relative text."""
    formatted: list[dict[str, Any]] = []
    for item in evidence:
        path = item.get("path")
        formatted.append(
            {
                "source": str(item.get("source") or "report"),
                "path": format_path(path, root)
                if isinstance(path, Path)
                else str(path),
                "summary": str(item.get("summary") or ""),
            }
        )
    return formatted


def unique_candidates(candidates: list[BacklogCandidate]) -> list[BacklogCandidate]:
    """Deduplicate candidates by stable id."""
    by_id: dict[str, BacklogCandidate] = {}
    for candidate in candidates:
        by_id.setdefault(candidate.id, candidate)
    return [by_id[key] for key in sorted(by_id)]


def slugify(value: str) -> str:
    """Create a stable id fragment from human text."""
    slug = re.sub(r"[^A-Za-z0-9_]+", "-", value.strip().lower()).strip("-")
    return slug or "unknown"


def int_value(value: object) -> int:
    """Return an integer value, or zero when absent or invalid."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _unobserved_backlog_closure_reason(
    item: dict[str, Any],
    *,
    root: Path | None = None,
    live_signals: dict[str, Any] | None = None,
    generated_at: str | None = None,
) -> str:
    """Return a more specific closure reason for freshness-guarded backlog items."""
    category = str(item.get("category") or "").strip()
    if not root or not isinstance(live_signals, dict):
        return "not_observed_in_latest_inspection"
    current_branch = str(live_signals.get("current_branch") or "").strip() or None
    current_head = str(live_signals.get("current_head") or "").strip() or None
    if category == "commit_isolation_gap":
        if not has_live_worktree_changes(
            live_signals
        ) or not has_commit_isolation_worktree_pressure(live_signals):
            return "freshness_guard_not_satisfied"
        from qa_z.worktree_discovery import commit_isolation_evidence

        if not commit_isolation_evidence(
            root,
            generated_at=generated_at,
            current_branch=current_branch,
            current_head=current_head,
        ):
            return "freshness_guard_not_satisfied"
    if category == "integration_gap":
        if not has_live_worktree_changes(
            live_signals
        ) or not has_non_current_truth_worktree_pressure(live_signals):
            return "freshness_guard_not_satisfied"
        from qa_z.worktree_discovery import integration_gap_evidence

        if not integration_gap_evidence(
            root,
            generated_at=generated_at,
            current_branch=current_branch,
            current_head=current_head,
        ):
            return "freshness_guard_not_satisfied"
    if category == "deferred_cleanup_gap":
        if not has_cleanup_artifact_pressure(live_signals):
            return "freshness_guard_not_satisfied"
        from qa_z.worktree_discovery import deferred_cleanup_evidence

        if not deferred_cleanup_evidence(
            root,
            generated_at=generated_at,
            current_branch=current_branch,
            current_head=current_head,
        ):
            return "freshness_guard_not_satisfied"
    return "not_observed_in_latest_inspection"
