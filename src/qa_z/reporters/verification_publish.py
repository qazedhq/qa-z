"""Publish-ready summaries for verification and repair-session outcomes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound, RunSource
from qa_z.artifacts import format_path, resolve_path
from qa_z.repair_session import load_repair_session, load_session_dry_run_summary

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


def detect_publish_summary_for_run(
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


def build_verification_publish_summary(
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


def load_session_publish_summary(
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


def build_session_verification_publish_summary(
    *,
    root: Path,
    verify_dir: Path,
    artifacts: PublishArtifactPaths,
) -> VerificationPublishSummary:
    """Build a session-flavored verification publish summary from verify artifacts."""
    summary = build_verification_publish_summary(root=root, verify_dir=verify_dir)
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


def render_publish_summary_markdown(
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
        action_text = recommended_action_summary_text(
            summary.executor_dry_run_recommended_actions
        )
        if action_text:
            lines.append(f"- Dry-run recommended actions: {action_text}")
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


def failed_verification_publish_summary(
    artifacts: PublishArtifactPaths,
    *,
    source: PublishSource = "verification",
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


def publish_headline(
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


def action_needed_for(*, recommendation: str, regression_count: int) -> str | None:
    """Return a short action line for non-happy paths."""
    if recommendation == "safe_to_review":
        return None
    if recommendation == "review_required":
        if regression_count > 0:
            return "Inspect regressions before merge."
        return "Review remaining blockers before merge."
    if recommendation == "do_not_merge":
        return "Do not merge until new or regressed blockers are fixed."
    if recommendation == "rerun_required":
        return "Rerun verification before merge."
    return "Continue repair; no blockers were resolved."


def render_key_artifacts(paths: PublishArtifactPaths) -> list[str]:
    """Render artifact paths that are present."""
    lines: list[str] = []
    if paths.session:
        lines.append(f"- Session: `{paths.session}`")
    if paths.verify_summary:
        lines.append(f"- Verify summary: `{paths.verify_summary}`")
    if paths.verify_compare:
        lines.append(f"- Verify compare: `{paths.verify_compare}`")
    if paths.verify_report:
        lines.append(f"- Verify report: `{paths.verify_report}`")
    if paths.outcome:
        lines.append(f"- Outcome: `{paths.outcome}`")
    if paths.handoff:
        lines.append(f"- Handoff: `{paths.handoff}`")
    return lines


def read_json_object(path: Path) -> dict[str, Any]:
    """Load a JSON object artifact with QA-Z artifact errors."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactLoadError(f"Could not read artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"Artifact is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError(f"Artifact must contain a JSON object: {path}")
    return data


def session_summary_path_from_manifest(
    *, root: Path, session_dir: Path, manifest: dict[str, Any]
) -> Path:
    """Return the session summary artifact path."""
    return (
        path_from_manifest(root, manifest, "summary_path")
        or session_dir / "summary.json"
    )


def resolve_session_dir(root: Path, session: str | Path) -> Path:
    """Resolve a session id, directory, or session.json path."""
    path = Path(session).expanduser()
    if path.name == "session.json":
        path = path.parent
    elif not path.is_absolute() and len(path.parts) == 1:
        path = root / ".qa-z" / "sessions" / path
    elif not path.is_absolute():
        path = root / path
    return path.resolve()


def containing_session_dir(*, root: Path, run_dir: Path) -> Path | None:
    """Return the enclosing repair-session directory for session-local runs."""
    sessions_root = (root / ".qa-z" / "sessions").resolve()
    try:
        relative = run_dir.resolve().relative_to(sessions_root)
    except ValueError:
        return None
    if len(relative.parts) < 2:
        return None
    session_dir = sessions_root / relative.parts[0]
    if (session_dir / "session.json").is_file():
        return session_dir
    return None


def run_id_from_compare(compare: dict[str, Any], side: str) -> str | None:
    """Return baseline/candidate run id from compare data."""
    direct = first_text(compare.get(f"{side}_run_id"))
    if direct:
        return direct
    side_data = mapping_value(compare.get(side))
    return path_name(first_text(side_data.get("run_dir")))


def path_from_manifest(root: Path, manifest: dict[str, Any], key: str) -> Path | None:
    """Resolve a manifest path value if present."""
    value = first_text(manifest.get(key))
    if not value:
        return None
    return resolve_path(root, value)


def path_from_nested_manifest(
    root: Path,
    manifest: dict[str, Any],
    container_key: str,
    key: str,
) -> Path | None:
    """Resolve a nested manifest artifact path value if present."""
    container = mapping_value(manifest.get(container_key))
    value = first_text(container.get(key))
    if not value:
        return None
    return resolve_path(root, value)


def mapping_value(value: object) -> dict[str, Any]:
    """Return a mapping value or an empty mapping."""
    if isinstance(value, dict):
        return value
    return {}


def int_value(*values: object) -> int:
    """Return the first integer-like value from a sequence."""
    for value in values:
        if value is None:
            continue
        try:
            return int(str(value))
        except (TypeError, ValueError):
            continue
    return 0


def first_text(*values: object) -> str | None:
    """Return the first non-empty string-like value."""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def path_name(value: str | None) -> str | None:
    """Return the final path component from a string path."""
    if not value:
        return None
    return Path(value).name or value


def string_list(value: object) -> list[str]:
    """Return a normalized string list from JSON-safe data."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def recommended_action_list(value: object) -> list[dict[str, str]]:
    """Return normalized recommended dry-run action objects."""
    if not isinstance(value, list):
        return []
    actions: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action_id = first_text(item.get("id"))
        summary = first_text(item.get("summary"))
        if action_id and summary:
            actions.append({"id": action_id, "summary": summary})
    return actions


def recommended_action_summary_text(value: object) -> str:
    """Render dry-run action summaries as one compact publish line."""
    return "; ".join(action["summary"] for action in recommended_action_list(value))
