"""Publish-ready summaries for verification and repair-session outcomes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound, RunSource
from qa_z.artifacts import format_path, resolve_path
from qa_z.operator_action_render import render_recommended_action_lines
from qa_z.repair_session import load_repair_session, load_session_dry_run_summary
from qa_z.reporters.verification_publish_loading import (
    build_verification_publish_summary,
    detect_publish_summary_for_run,
    load_session_publish_summary,
)
from qa_z.reporters.verification_publish_render import (
    publish_headline,
    render_publish_summary_markdown,
)
from qa_z.reporters.verification_publish_models import (
    PublishArtifactPaths,
    PublishSource,
    SessionPublishSummary,
    VerificationPublishSummary,
)
from qa_z.reporters.verification_publish_summary import (
    build_session_verification_publish_summary,
    failed_verification_publish_summary,
    recommendation_for_verdict,
    verification_publish_summary_from_session,
)
from qa_z.reporters.verification_publish_support import (
    action_needed_for,
    containing_session_dir,
    first_text,
    int_value,
    mapping_value,
    path_from_manifest,
    path_from_nested_manifest,
    read_json_object,
    recommended_action_list,
    render_key_artifacts,
    resolve_session_dir,
    run_id_from_compare,
    session_summary_path_from_manifest,
    string_list,
)

__all__ = [
    "PublishArtifactPaths",
    "PublishSource",
    "SessionPublishSummary",
    "VerificationPublishSummary",
    "action_needed_for",
    "build_session_verification_publish_summary",
    "build_verification_publish_summary",
    "containing_session_dir",
    "detect_publish_summary_for_run",
    "failed_verification_publish_summary",
    "load_publish_dry_run_summary",
    "load_session_publish_summary",
    "publish_headline",
    "read_json_object",
    "recommendation_for_verdict",
    "render_key_artifacts",
    "render_publish_summary_markdown",
    "resolve_session_dir",
    "session_artifact_paths",
    "session_summary_path_from_manifest",
    "verification_publish_summary_from_session",
]


def _detect_publish_summary_for_run_impl(
    *, root: Path, run_source: RunSource
) -> VerificationPublishSummary | SessionPublishSummary | None:
    """Find a publishable repair outcome related to a run, if one exists."""
    session_summary = discover_session_publish_summary(root=root, run_source=run_source)
    if session_summary is not None:
        return session_summary

    verify_dir = run_source.run_dir / "verify"
    if verify_dir.exists():
        return build_verification_publish_summary(root=root, verify_dir=verify_dir)
    return None


def _build_verification_publish_summary_impl(
    *, root: Path, verify_dir: Path
) -> VerificationPublishSummary:
    """Build a concise publish summary from verification artifacts."""
    summary_path = verify_dir / "summary.json"
    compare_path = verify_dir / "compare.json"
    report_path = verify_dir / "report.md"
    artifacts = PublishArtifactPaths(
        verify_summary=format_path(summary_path, root),
        verify_compare=format_path(compare_path, root),
        verify_report=format_path(report_path, root),
    )
    try:
        summary = read_json_object(summary_path)
        compare = read_json_object(compare_path)
    except ArtifactLoadError:
        return failed_verification_publish_summary(artifacts)

    compare_summary = mapping_value(compare.get("summary"))
    verdict = first_text(summary.get("verdict"), compare.get("verdict"))
    if not verdict:
        verdict = "verification_failed"
    resolved_count = int_value(
        summary.get("resolved_count"), compare_summary.get("resolved_count")
    )
    remaining_count = int_value(
        summary.get("blocking_after"), compare_summary.get("blocking_after")
    )
    regression_count = int_value(
        summary.get("regression_count"), compare_summary.get("regression_count")
    )
    recommendation = recommendation_for_verdict(verdict)
    return VerificationPublishSummary(
        baseline_run_id=run_id_from_compare(compare, "baseline"),
        candidate_run_id=run_id_from_compare(compare, "candidate"),
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
        action_needed=action_needed_for(
            recommendation=recommendation,
            regression_count=regression_count,
        ),
    )


def _load_session_publish_summary_impl(
    *, root: Path, session: str | Path
) -> SessionPublishSummary:
    """Build a concise publish summary from a repair-session directory."""
    session_dir = resolve_session_dir(root, session)
    manifest_path = session_dir / "session.json"
    if not manifest_path.is_file():
        raise ArtifactSourceNotFound(f"Repair session not found: {session_dir}")

    try:
        manifest = read_json_object(manifest_path)
    except ArtifactLoadError as exc:
        raise ArtifactLoadError(
            f"Could not read repair session: {manifest_path}"
        ) from exc

    session_id = first_text(manifest.get("session_id")) or session_dir.name
    state = first_text(manifest.get("state")) or "unknown"
    session_summary_path = session_summary_path_from_manifest(
        root=root,
        session_dir=session_dir,
        manifest=manifest,
    )
    artifacts = session_artifact_paths(
        root=root,
        session_dir=session_dir,
        manifest_path=manifest_path,
        manifest=manifest,
    )
    verify_dir = (
        path_from_manifest(root, manifest, "verify_dir") or session_dir / "verify"
    )
    dry_run_summary = load_publish_dry_run_summary(root=root, session_ref=session_dir)
    try:
        session_summary = read_json_object(session_summary_path)
    except ArtifactLoadError:
        verification = build_session_verification_publish_summary(
            root=root,
            verify_dir=verify_dir,
            artifacts=artifacts,
        )
        return SessionPublishSummary(
            session_id=session_id,
            state=state,
            verification=verification,
            artifacts=artifacts,
            executor_dry_run_verdict=first_text(dry_run_summary.get("verdict")),
            executor_dry_run_reason=first_text(dry_run_summary.get("verdict_reason")),
            executor_dry_run_source=first_text(dry_run_summary.get("summary_source")),
            executor_dry_run_attempt_count=int_value(
                dry_run_summary.get("evaluated_attempt_count")
            ),
            executor_dry_run_history_signals=string_list(
                dry_run_summary.get("history_signals")
            ),
            executor_dry_run_operator_decision=first_text(
                dry_run_summary.get("operator_decision")
            ),
            executor_dry_run_operator_summary=first_text(
                dry_run_summary.get("operator_summary")
            ),
            executor_dry_run_recommended_actions=recommended_action_list(
                dry_run_summary.get("recommended_actions")
            ),
        )

    verification = verification_publish_summary_from_session(
        session_summary=session_summary,
        artifacts=artifacts,
    )
    return SessionPublishSummary(
        session_id=session_id,
        state=state,
        verification=verification,
        artifacts=artifacts,
        executor_dry_run_verdict=first_text(
            session_summary.get("executor_dry_run_verdict"),
            dry_run_summary.get("verdict"),
        ),
        executor_dry_run_reason=first_text(
            session_summary.get("executor_dry_run_reason"),
            dry_run_summary.get("verdict_reason"),
        ),
        executor_dry_run_source=first_text(
            session_summary.get("executor_dry_run_source"),
            dry_run_summary.get("summary_source"),
        ),
        executor_dry_run_attempt_count=int_value(
            session_summary.get("executor_dry_run_attempt_count"),
            dry_run_summary.get("evaluated_attempt_count"),
        ),
        executor_dry_run_history_signals=string_list(
            session_summary.get("executor_dry_run_history_signals")
        )
        or string_list(dry_run_summary.get("history_signals")),
        executor_dry_run_operator_decision=first_text(
            session_summary.get("executor_dry_run_operator_decision"),
            dry_run_summary.get("operator_decision"),
        ),
        executor_dry_run_operator_summary=first_text(
            session_summary.get("executor_dry_run_operator_summary"),
            dry_run_summary.get("operator_summary"),
        ),
        executor_dry_run_recommended_actions=recommended_action_list(
            session_summary.get("executor_dry_run_recommended_actions")
        )
        or recommended_action_list(dry_run_summary.get("recommended_actions")),
    )


def load_publish_dry_run_summary(
    *, root: Path, session_ref: str | Path
) -> dict[str, Any]:
    """Load or synthesize additive dry-run context for publish surfaces."""
    try:
        session = load_repair_session(root, str(session_ref))
    except ArtifactLoadError:
        return {}
    return load_session_dry_run_summary(session, root) or {}


def discover_session_publish_summary(
    *, root: Path, run_source: RunSource
) -> SessionPublishSummary | None:
    """Find a completed session whose candidate run matches this run."""
    direct_session_dir = containing_session_dir(root=root, run_dir=run_source.run_dir)
    if direct_session_dir is not None:
        return load_session_publish_summary(root=root, session=direct_session_dir)

    sessions_root = root / ".qa-z" / "sessions"
    if not sessions_root.is_dir():
        return None

    matches: list[tuple[str, Path]] = []
    for manifest_path in sessions_root.glob("*/session.json"):
        try:
            manifest = read_json_object(manifest_path)
        except ArtifactLoadError:
            continue
        candidate_run_dir = first_text(manifest.get("candidate_run_dir"))
        if not candidate_run_dir:
            continue
        if resolve_path(root, candidate_run_dir) != run_source.run_dir.resolve():
            continue
        updated_at = first_text(manifest.get("updated_at")) or ""
        matches.append((updated_at, manifest_path.parent))

    if not matches:
        return None
    _updated_at, session_dir = sorted(matches, key=lambda item: item[0])[-1]
    return load_session_publish_summary(root=root, session=session_dir)


def _render_publish_summary_markdown_impl(
    summary: VerificationPublishSummary | SessionPublishSummary,
) -> str:
    """Render concise Markdown suitable for a GitHub Actions Job Summary."""
    if isinstance(summary, SessionPublishSummary):
        title = "Repair Session Outcome"
        verification = summary.verification
        artifacts = summary.artifacts
    else:
        title = "Repair Verification Outcome"
        verification = summary
        artifacts = summary.artifacts

    lines = [f"## {title}", "", verification.headline, ""]
    if isinstance(summary, SessionPublishSummary):
        lines.append(f"- Session state: {summary.state}")
        if summary.executor_dry_run_verdict:
            lines.append(f"- Executor dry-run: {summary.executor_dry_run_verdict}")
        if summary.executor_dry_run_reason:
            lines.append(f"- Dry-run reason: {summary.executor_dry_run_reason}")
        if summary.executor_dry_run_source:
            lines.append(f"- Dry-run source: {summary.executor_dry_run_source}")
        if summary.executor_dry_run_attempt_count:
            lines.append(
                f"- Executor attempts: {summary.executor_dry_run_attempt_count}"
            )
        if summary.executor_dry_run_history_signals:
            lines.append(
                "- Executor history signals: "
                + ", ".join(summary.executor_dry_run_history_signals),
            )
        if summary.executor_dry_run_operator_decision:
            lines.append(
                "- Dry-run operator decision: "
                + summary.executor_dry_run_operator_decision
            )
        if summary.executor_dry_run_operator_summary:
            lines.append(
                "- Dry-run operator summary: "
                + summary.executor_dry_run_operator_summary
            )
        action_lines = render_recommended_action_lines(
            summary.executor_dry_run_recommended_actions,
            include_action_label=True,
        )
        if action_lines != ["- none"]:
            lines.append("- Dry-run recommended actions:")
            lines.extend(action_lines)
    lines.extend(
        [
            f"- Verdict: {verification.final_verdict}",
            f"- Resolved blockers: {verification.resolved_count}",
            f"- Remaining blockers: {verification.remaining_blocker_count}",
            f"- Regressions: {verification.regression_count}",
            f"- Recommendation: {verification.recommendation}",
        ]
    )

    artifact_lines = render_key_artifacts(artifacts)
    if artifact_lines:
        lines.extend(["", "### Key Artifacts", *artifact_lines])

    if verification.action_needed:
        lines.extend(["", "### Action Needed", verification.action_needed])
    return "\n".join(lines).strip() + "\n"


def session_artifact_paths(
    *,
    root: Path,
    session_dir: Path,
    manifest_path: Path,
    manifest: dict[str, Any],
) -> PublishArtifactPaths:
    """Extract stable session artifact paths for concise summaries."""
    verify_dir = (
        path_from_manifest(root, manifest, "verify_dir") or session_dir / "verify"
    )
    handoff_json = path_from_nested_manifest(
        root, manifest, "handoff_artifacts", "handoff_json"
    )
    return PublishArtifactPaths(
        session=format_path(manifest_path, root),
        verify_summary=format_path(
            path_from_nested_manifest(
                root, manifest, "verify_artifacts", "summary_json"
            )
            or verify_dir / "summary.json",
            root,
        ),
        verify_compare=format_path(
            path_from_nested_manifest(
                root, manifest, "verify_artifacts", "compare_json"
            )
            or verify_dir / "compare.json",
            root,
        ),
        verify_report=format_path(
            path_from_nested_manifest(
                root, manifest, "verify_artifacts", "report_markdown"
            )
            or verify_dir / "report.md",
            root,
        ),
        outcome=format_path(
            path_from_manifest(root, manifest, "outcome_path")
            or session_dir / "outcome.md",
            root,
        ),
        handoff=format_path(handoff_json, root) if handoff_json is not None else None,
    )


def _publish_headline_impl(
    *,
    verdict: str,
    resolved_count: int,
    remaining_count: int,
    regression_count: int,
) -> str:
    """Return a short outcome headline."""
    if verdict == "verification_failed":
        return "Verification artifacts could not be read."
    return (
        f"{verdict}: {resolved_count} resolved, "
        f"{remaining_count} remaining, {regression_count} regressions."
    )
