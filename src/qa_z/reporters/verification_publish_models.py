"""Shared data models for verification-publish surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PublishSource = Literal["verification", "session"]


@dataclass(frozen=True)
class PublishArtifactPaths:
    """Short artifact paths worth surfacing in GitHub summaries."""

    session: str | None = None
    verify_summary: str | None = None
    verify_compare: str | None = None
    verify_report: str | None = None
    outcome: str | None = None
    handoff: str | None = None


@dataclass(frozen=True)
class VerificationPublishSummary:
    """Concise verification outcome for CI and PR-facing surfaces."""

    baseline_run_id: str | None
    candidate_run_id: str | None
    final_verdict: str
    resolved_count: int
    remaining_blocker_count: int
    regression_count: int
    recommendation: str
    artifacts: PublishArtifactPaths
    headline: str
    source: PublishSource = "verification"
    action_needed: str | None = None


@dataclass(frozen=True)
class SessionPublishSummary:
    """Concise repair-session outcome for CI and PR-facing surfaces."""

    session_id: str
    state: str
    verification: VerificationPublishSummary
    artifacts: PublishArtifactPaths
    executor_dry_run_verdict: str | None = None
    executor_dry_run_reason: str | None = None
    executor_dry_run_source: str | None = None
    executor_dry_run_attempt_count: int | None = None
    executor_dry_run_history_signals: list[str] | None = None
    executor_dry_run_operator_decision: str | None = None
    executor_dry_run_operator_summary: str | None = None
    executor_dry_run_recommended_actions: list[dict[str, str]] | None = None


__all__ = [
    "PublishArtifactPaths",
    "PublishSource",
    "SessionPublishSummary",
    "VerificationPublishSummary",
]
