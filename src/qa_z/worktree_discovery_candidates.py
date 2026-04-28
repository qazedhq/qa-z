"""Candidate builders for worktree-related self-improvement discovery."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.backlog_core import BacklogCandidate, int_value
from qa_z.live_repository import (
    dirty_benchmark_result_paths,
    generated_artifact_policy_evidence,
    generated_artifact_policy_is_explicit,
    has_cleanup_artifact_pressure,
    has_commit_isolation_worktree_pressure,
    has_live_worktree_changes,
    has_non_current_truth_worktree_pressure,
    list_signal_paths,
    sample_signal_paths,
    worktree_area_summary,
)
from qa_z.self_improvement_constants import (
    DIRTY_WORKTREE_MODIFIED_THRESHOLD,
    DIRTY_WORKTREE_TOTAL_THRESHOLD,
)
from qa_z.worktree_discovery_evidence import (
    artifact_hygiene_evidence,
    commit_isolation_evidence,
    deferred_cleanup_evidence,
    evidence_freshness_evidence,
    integration_gap_evidence,
)


def discover_worktree_risk_candidates(
    root: Path, live_signals: dict[str, Any], *, generated_at: str | None = None
) -> list[Any]:
    """Create candidates from large live dirty-worktree signals."""
    modified = int_value(live_signals.get("modified_count"))
    untracked = int_value(live_signals.get("untracked_count"))
    staged = int_value(live_signals.get("staged_count"))
    total_dirty = modified + untracked
    if modified < DIRTY_WORKTREE_MODIFIED_THRESHOLD and (
        total_dirty <= DIRTY_WORKTREE_TOTAL_THRESHOLD
    ):
        return []
    dirty_paths = list_signal_paths(live_signals, "modified_paths") + list_signal_paths(
        live_signals, "untracked_paths"
    )
    sample_paths = sample_signal_paths(dirty_paths)
    summary = f"modified={modified}; untracked={untracked}; staged={staged}"
    area_summary = worktree_area_summary(dirty_paths)
    if area_summary:
        summary += "; areas=" + area_summary
    if sample_paths:
        summary += "; sample=" + ", ".join(sample_paths)
    signals = ["dirty_worktree_large", "worktree_integration_risk"]
    if staged > 0:
        signals.append("staged_changes_present")
    evidence = [
        {
            "source": "git_status",
            "path": ".",
            "summary": summary,
        }
    ]
    evidence.extend(
        integration_gap_evidence(
            root,
            generated_at=generated_at,
            current_branch=str(live_signals.get("current_branch") or "").strip()
            or None,
            current_head=str(live_signals.get("current_head") or "").strip() or None,
        )
    )
    return [
        BacklogCandidate(
            id="worktree_risk-dirty-worktree",
            title="Reduce dirty worktree integration risk",
            category="worktree_risk",
            evidence=evidence,
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=3,
            recommendation="reduce_integration_risk",
            signals=signals,
        )
    ]


def discover_deferred_cleanup_candidates(
    root: Path, live_signals: dict[str, Any], *, generated_at: str | None = None
) -> list[Any]:
    """Create candidates from deferred cleanup notes and generated output drift."""
    if not has_cleanup_artifact_pressure(live_signals):
        return []
    evidence = deferred_cleanup_evidence(
        root,
        generated_at=generated_at,
        current_branch=str(live_signals.get("current_branch") or "").strip() or None,
        current_head=str(live_signals.get("current_head") or "").strip() or None,
    )
    benchmark_paths = (
        []
        if generated_artifact_policy_is_explicit(live_signals)
        else dirty_benchmark_result_paths(live_signals)
    )
    if benchmark_paths and evidence:
        evidence.append(
            {
                "source": "generated_outputs",
                "path": benchmark_paths[0],
                "summary": (
                    "generated benchmark outputs still present: "
                    + ", ".join(sample_signal_paths(benchmark_paths))
                ),
            }
        )
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="deferred_cleanup_gap-worktree-deferred-items",
            title="Triage deferred cleanup items before they drift further",
            category="deferred_cleanup_gap",
            evidence=evidence,
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=3,
            recommendation="triage_and_isolate_changes",
            signals=["deferred_cleanup_repeated", "worktree_integration_risk"],
        )
    ]


def discover_commit_isolation_candidates(
    root: Path, live_signals: dict[str, Any], *, generated_at: str | None = None
) -> list[Any]:
    """Create candidates from commit-order dependency evidence."""
    if not has_live_worktree_changes(
        live_signals
    ) or not has_commit_isolation_worktree_pressure(live_signals):
        return []
    evidence = commit_isolation_evidence(
        root,
        generated_at=generated_at,
        current_branch=str(live_signals.get("current_branch") or "").strip() or None,
        current_head=str(live_signals.get("current_head") or "").strip() or None,
    )
    modified = int_value(live_signals.get("modified_count"))
    untracked = int_value(live_signals.get("untracked_count"))
    if evidence and (modified or untracked):
        dirty_paths = list_signal_paths(
            live_signals, "modified_paths"
        ) + list_signal_paths(live_signals, "untracked_paths")
        summary = (
            f"dirty worktree still spans modified={modified}; untracked={untracked}"
        )
        area_summary = worktree_area_summary(dirty_paths)
        if area_summary:
            summary += "; areas=" + area_summary
        evidence.append(
            {
                "source": "git_status",
                "path": ".",
                "summary": summary,
            }
        )
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="commit_isolation_gap-foundation-order",
            title="Isolate the foundation commit before later batches",
            category="commit_isolation_gap",
            evidence=evidence,
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=4,
            recommendation="isolate_foundation_commit",
            signals=["commit_order_dependency_exists", "worktree_integration_risk"],
        )
    ]


def discover_artifact_hygiene_candidates(
    root: Path, live_signals: dict[str, Any]
) -> list[Any]:
    """Create candidates from runtime/source artifact separation gaps."""
    policy_explicit = generated_artifact_policy_is_explicit(live_signals)
    runtime_paths = list_signal_paths(live_signals, "runtime_artifact_paths")
    if policy_explicit and not runtime_paths:
        return []
    evidence = artifact_hygiene_evidence(root)
    benchmark_paths = (
        []
        if policy_explicit
        else list_signal_paths(live_signals, "benchmark_result_paths")
    )
    mixed_paths = sample_signal_paths(runtime_paths + benchmark_paths)
    if evidence or runtime_paths:
        evidence.append(
            {
                "source": "runtime_artifacts",
                "path": mixed_paths[0] if mixed_paths else ".",
                "summary": (
                    "runtime or generated artifacts are still mixed into the "
                    "repository surface: "
                    + ", ".join(
                        mixed_paths or ["runtime artifact policy remains ambiguous"]
                    )
                ),
            }
        )
    if not evidence:
        return []
    signals = ["worktree_integration_risk"]
    if policy_explicit and runtime_paths:
        signals.insert(0, "runtime_artifact_source_mixing")
    else:
        signals.insert(0, "generated_artifact_policy_ambiguity")
    return [
        BacklogCandidate(
            id="artifact_hygiene_gap-runtime-source-separation",
            title="Separate runtime artifacts from source-tracked evidence",
            category="artifact_hygiene_gap",
            evidence=evidence,
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=3,
            recommendation="separate_runtime_from_source_artifacts",
            signals=signals,
        )
    ]


def discover_runtime_artifact_cleanup_candidates(
    root: Path, live_signals: dict[str, Any]
) -> list[Any]:
    """Create candidates when generated benchmark/runtime artifacts need cleanup."""
    policy_explicit = generated_artifact_policy_is_explicit(live_signals)
    live_runtime_paths = list_signal_paths(live_signals, "runtime_artifact_paths")
    if policy_explicit and not live_runtime_paths:
        return []
    benchmark_paths = (
        []
        if policy_explicit
        else list_signal_paths(live_signals, "benchmark_result_paths")
    )
    report_evidence = deferred_cleanup_evidence(root) or artifact_hygiene_evidence(root)
    if not live_runtime_paths and not report_evidence:
        return []
    runtime_paths = sample_signal_paths(live_runtime_paths + benchmark_paths)
    if not runtime_paths:
        return []
    evidence = list(report_evidence)
    evidence.append(
        {
            "source": "runtime_artifacts",
            "path": runtime_paths[0],
            "summary": "generated runtime artifacts need explicit cleanup handling: "
            + ", ".join(runtime_paths),
        }
    )
    signals = ["worktree_integration_risk"]
    impact = 3
    if policy_explicit and live_runtime_paths:
        signals.insert(0, "policy_managed_runtime_artifacts")
        impact = 4
    else:
        signals.insert(0, "generated_artifact_policy_ambiguity")
    return [
        BacklogCandidate(
            id="runtime_artifact_cleanup_gap-generated-results",
            title="Clean up generated runtime artifacts before source integration",
            category="runtime_artifact_cleanup_gap",
            evidence=evidence,
            impact=impact,
            likelihood=4,
            confidence=4,
            repair_cost=3,
            recommendation="triage_and_isolate_changes",
            signals=signals,
        )
    ]


def discover_evidence_freshness_candidates(
    root: Path, live_signals: dict[str, Any]
) -> list[Any]:
    """Create candidates from ambiguous frozen-vs-generated evidence handling."""
    if generated_artifact_policy_is_explicit(live_signals):
        return []
    evidence = evidence_freshness_evidence(root)
    benchmark_paths = (
        []
        if generated_artifact_policy_is_explicit(live_signals)
        else list_signal_paths(live_signals, "benchmark_result_paths")
    )
    policy_evidence = generated_artifact_policy_evidence(root, live_signals)
    if policy_evidence and (
        evidence or list_signal_paths(live_signals, "runtime_artifact_paths")
    ):
        evidence.extend(policy_evidence)
    if benchmark_paths and evidence:
        evidence.append(
            {
                "source": "benchmark_results",
                "path": benchmark_paths[0],
                "summary": (
                    "benchmark result artifacts exist without a clear frozen-evidence "
                    "decision: " + ", ".join(sample_signal_paths(benchmark_paths))
                ),
            }
        )
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="evidence_freshness_gap-generated-vs-frozen-policy",
            title="Clarify generated versus frozen evidence policy",
            category="evidence_freshness_gap",
            evidence=evidence,
            impact=3,
            likelihood=4,
            confidence=4,
            repair_cost=2,
            recommendation="clarify_generated_vs_frozen_evidence_policy",
            signals=["generated_artifact_policy_ambiguity"],
        )
    ]


def discover_integration_gap_candidates(
    root: Path, live_signals: dict[str, Any], *, generated_at: str | None = None
) -> list[Any]:
    """Create candidates from broad worktree integration drift evidence."""
    if not has_non_current_truth_worktree_pressure(live_signals):
        return []
    evidence = integration_gap_evidence(
        root,
        generated_at=generated_at,
        current_branch=str(live_signals.get("current_branch") or "").strip() or None,
        current_head=str(live_signals.get("current_head") or "").strip() or None,
    )
    if not evidence:
        return []
    dirty_paths = list_signal_paths(live_signals, "modified_paths") + list_signal_paths(
        live_signals, "untracked_paths"
    )
    modified = int_value(live_signals.get("modified_count"))
    untracked = int_value(live_signals.get("untracked_count"))
    staged = int_value(live_signals.get("staged_count"))
    summary = (
        f"integration worktree spans modified={modified}; "
        f"untracked={untracked}; staged={staged}"
    )
    area_summary = worktree_area_summary(dirty_paths)
    if area_summary:
        summary += "; areas=" + area_summary
    evidence.append(
        {
            "source": "git_status",
            "path": ".",
            "summary": summary,
        }
    )
    return [
        BacklogCandidate(
            id="integration_gap-worktree-integration-risk",
            title="Audit worktree integration and commit-split risk",
            category="integration_gap",
            evidence=evidence,
            impact=2,
            likelihood=3,
            confidence=4,
            repair_cost=2,
            recommendation="audit_worktree_integration",
            signals=["worktree_integration_risk"],
        )
    ]
