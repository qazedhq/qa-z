"""Grouped discovery-stage definitions for self-improvement inspection."""

from __future__ import annotations

from qa_z.discovery_pipeline import DiscoveryStage
from qa_z.execution_discovery import (
    discover_executor_contract_candidates,
    discover_executor_history_candidates,
    discover_executor_ingest_candidates,
    discover_executor_result_candidates,
    discover_session_candidates,
    discover_verification_candidates,
)
from qa_z.self_improvement_discovery import (
    discover_backlog_reseeding_candidates,
    discover_benchmark_candidates,
    discover_empty_loop_candidates,
    discover_repeated_fallback_family_candidates,
)
from qa_z.surface_discovery import (
    discover_artifact_consistency_candidates,
    discover_coverage_gap_candidates,
    discover_docs_drift_candidates,
)
from qa_z.worktree_discovery import (
    discover_artifact_hygiene_candidates,
    discover_commit_isolation_candidates,
    discover_deferred_cleanup_candidates,
    discover_evidence_freshness_candidates,
    discover_integration_gap_candidates,
    discover_runtime_artifact_cleanup_candidates,
    discover_worktree_risk_candidates,
)

__all__ = [
    "BASELINE_DISCOVERY_STAGES",
    "EXECUTION_CONTRACT_DISCOVERY_STAGES",
    "EXECUTION_DISCOVERY_STAGES",
    "LOOP_HEALTH_DISCOVERY_STAGES",
    "SURFACE_DISCOVERY_STAGES",
    "WORKTREE_DISCOVERY_STAGES",
]

BASELINE_DISCOVERY_STAGES = [
    DiscoveryStage(
        "benchmark",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_benchmark_candidates(root)
        ),
    ),
]

EXECUTION_DISCOVERY_STAGES = [
    DiscoveryStage(
        "verification",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_verification_candidates(root)
        ),
    ),
    DiscoveryStage(
        "session",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_session_candidates(root)
        ),
    ),
    DiscoveryStage(
        "executor_result",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_executor_result_candidates(root)
        ),
    ),
    DiscoveryStage(
        "executor_ingest",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_executor_ingest_candidates(root)
        ),
    ),
    DiscoveryStage(
        "executor_history",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_executor_history_candidates(root)
        ),
    ),
]

EXECUTION_CONTRACT_DISCOVERY_STAGES = [
    DiscoveryStage(
        "executor_contract",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_executor_contract_candidates(root)
        ),
    ),
]

SURFACE_DISCOVERY_STAGES = [
    DiscoveryStage(
        "artifact_consistency",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_artifact_consistency_candidates(root)
        ),
    ),
    DiscoveryStage(
        "docs_drift",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_docs_drift_candidates(root)
        ),
    ),
    DiscoveryStage(
        "coverage_gap",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_coverage_gap_candidates(root)
        ),
    ),
]

WORKTREE_DISCOVERY_STAGES = [
    DiscoveryStage(
        "worktree_risk",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_worktree_risk_candidates(
                root, live_signals, generated_at=generated_at
            )
        ),
    ),
    DiscoveryStage(
        "deferred_cleanup",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_deferred_cleanup_candidates(
                root, live_signals, generated_at=generated_at
            )
        ),
    ),
    DiscoveryStage(
        "commit_isolation",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_commit_isolation_candidates(
                root, live_signals, generated_at=generated_at
            )
        ),
    ),
    DiscoveryStage(
        "artifact_hygiene",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_artifact_hygiene_candidates(root, live_signals)
        ),
    ),
    DiscoveryStage(
        "runtime_artifact_cleanup",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_runtime_artifact_cleanup_candidates(root, live_signals)
        ),
    ),
    DiscoveryStage(
        "evidence_freshness",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_evidence_freshness_candidates(root, live_signals)
        ),
    ),
    DiscoveryStage(
        "integration_gap",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_integration_gap_candidates(
                root, live_signals, generated_at=generated_at
            )
        ),
    ),
]

LOOP_HEALTH_DISCOVERY_STAGES = [
    DiscoveryStage(
        "empty_loop",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_empty_loop_candidates(root)
        ),
    ),
    DiscoveryStage(
        "fallback_family_repeat",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_repeated_fallback_family_candidates(root)
        ),
    ),
    DiscoveryStage(
        "backlog_reseeding",
        lambda root, backlog, candidates, live_signals, generated_at: (
            discover_backlog_reseeding_candidates(root, backlog, candidates)
        ),
    ),
]
