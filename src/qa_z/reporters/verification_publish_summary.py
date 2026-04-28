"""Summary-building helpers for verification-publish surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from qa_z.reporters.verification_publish_models import (
    PublishArtifactPaths,
    VerificationPublishSummary,
)
from qa_z.reporters.verification_publish_support import (
    action_needed_for,
    first_text,
    int_value,
    path_name,
)
from qa_z.reporters.verification_publish_render import publish_headline


def recommendation_for_verdict(verdict: str) -> str:
    """Map deterministic verification verdicts to PR-friendly next actions."""
    if verdict == "improved":
        return "safe_to_review"
    if verdict == "mixed":
        return "review_required"
    if verdict == "regressed":
        return "do_not_merge"
    if verdict == "verification_failed":
        return "rerun_required"
    return "continue_repair"


def build_session_verification_publish_summary(
    *,
    root: Path,
    verify_dir: Path,
    artifacts: PublishArtifactPaths,
) -> VerificationPublishSummary:
    """Build a session-flavored verification publish summary from verify artifacts."""
    from qa_z.reporters import verification_publish as verification_publish_module

    summary = verification_publish_module.build_verification_publish_summary(
        root=root,
        verify_dir=verify_dir,
    )
    return VerificationPublishSummary(
        baseline_run_id=summary.baseline_run_id,
        candidate_run_id=summary.candidate_run_id,
        final_verdict=summary.final_verdict,
        resolved_count=summary.resolved_count,
        remaining_blocker_count=summary.remaining_blocker_count,
        regression_count=summary.regression_count,
        recommendation=summary.recommendation,
        artifacts=artifacts,
        headline=summary.headline,
        source="session",
        action_needed=summary.action_needed,
    )


def verification_publish_summary_from_session(
    *,
    session_summary: dict[str, Any],
    artifacts: PublishArtifactPaths,
) -> VerificationPublishSummary:
    """Normalize a session summary into the verification publish shape."""
    verdict = first_text(session_summary.get("verdict")) or "verification_failed"
    resolved_count = int_value(session_summary.get("resolved_count"))
    remaining_count = int_value(
        session_summary.get("remaining_issue_count"),
        session_summary.get("blocking_after"),
    )
    regression_count = int_value(session_summary.get("regression_count"))
    recommendation = recommendation_for_verdict(verdict)
    return VerificationPublishSummary(
        baseline_run_id=path_name(first_text(session_summary.get("baseline_run_dir"))),
        candidate_run_id=path_name(
            first_text(session_summary.get("candidate_run_dir"))
        ),
        final_verdict=verdict,
        resolved_count=resolved_count,
        remaining_blocker_count=remaining_count,
        regression_count=regression_count,
        recommendation=recommendation,
        artifacts=artifacts,
        headline=publish_headline(
            verdict=verdict,
            resolved_count=resolved_count,
            remaining_count=remaining_count,
            regression_count=regression_count,
        ),
        source="session",
        action_needed=action_needed_for(
            recommendation=recommendation,
            regression_count=regression_count,
        ),
    )


def failed_verification_publish_summary(
    artifacts: PublishArtifactPaths,
    *,
    source: Literal["verification", "session"] = "verification",
) -> VerificationPublishSummary:
    """Return a publishable failure when verification artifacts cannot be read."""
    recommendation = recommendation_for_verdict("verification_failed")
    return VerificationPublishSummary(
        baseline_run_id=None,
        candidate_run_id=None,
        final_verdict="verification_failed",
        resolved_count=0,
        remaining_blocker_count=0,
        regression_count=0,
        recommendation=recommendation,
        artifacts=artifacts,
        headline="Verification artifacts could not be read.",
        source=source,
        action_needed=action_needed_for(
            recommendation=recommendation,
            regression_count=0,
        ),
    )
