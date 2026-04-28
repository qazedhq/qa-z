"""Support helpers for verification-publish loading and rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import ArtifactLoadError, resolve_path
from qa_z.reporters.verification_publish_models import PublishArtifactPaths


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
