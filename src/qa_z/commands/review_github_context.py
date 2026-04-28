"""Context loading helpers for GitHub summary command handling."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from qa_z.artifacts import RunSource, load_run_summary, resolve_run_source
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.verification_publish import (
    SessionPublishSummary,
    VerificationPublishSummary,
    detect_publish_summary_for_run,
    load_session_publish_summary,
)
from qa_z.repair_session import load_repair_session
from qa_z.runners.models import RunSummary


@dataclass(frozen=True)
class GitHubSummaryContext:
    """Resolved run, deep, and publish context for GitHub summaries."""

    run_source: RunSource
    summary: RunSummary
    deep_summary: RunSummary | None
    publish_summary: VerificationPublishSummary | SessionPublishSummary | None


def resolve_github_summary_run_source(
    *,
    root: Path,
    config: dict,
    from_run: str | None,
    from_session: str | None,
) -> RunSource:
    """Resolve the source run, preferring session candidate runs when explicit."""
    if from_session and from_run in (None, "", "latest"):
        session = load_repair_session(root, from_session)
        if session.candidate_run_dir:
            return resolve_run_source(root, config, session.candidate_run_dir)
    return resolve_run_source(root, config, from_run)


def load_github_summary_context(
    *,
    root: Path,
    config: dict,
    from_run: str | None,
    from_session: str | None,
) -> GitHubSummaryContext:
    """Load all artifacts needed to render a GitHub summary."""
    run_source = resolve_github_summary_run_source(
        root=root,
        config=config,
        from_run=from_run,
        from_session=from_session,
    )
    summary = load_run_summary(run_source.summary_path)
    deep_summary = load_sibling_deep_summary(run_source)
    publish_summary = (
        load_session_publish_summary(root=root, session=from_session)
        if from_session
        else detect_publish_summary_for_run(root=root, run_source=run_source)
    )
    return GitHubSummaryContext(
        run_source=run_source,
        summary=summary,
        deep_summary=deep_summary,
        publish_summary=publish_summary,
    )
