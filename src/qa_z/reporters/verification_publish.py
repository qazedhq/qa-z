"""Publishable summaries for QA-Z verification evidence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PUBLISH_SUMMARY_KIND = "qa_z.verification_publish_summary"
PUBLISH_SUMMARY_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class PublishSummary:
    """Compact verification status suitable for CI summaries."""

    source_type: str
    source_path: str
    verdict: str
    repair_improved: bool
    resolved_count: int
    remaining_issue_count: int
    new_issue_count: int
    regression_count: int
    not_comparable_count: int
    recommendation: str
    session_id: str | None = None
    kind: str = PUBLISH_SUMMARY_KIND
    schema_version: int = PUBLISH_SUMMARY_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Render this summary as JSON-safe data."""
        data: dict[str, Any] = {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "source_type": self.source_type,
            "source_path": self.source_path,
            "verdict": self.verdict,
            "repair_improved": self.repair_improved,
            "resolved_count": self.resolved_count,
            "remaining_issue_count": self.remaining_issue_count,
            "new_issue_count": self.new_issue_count,
            "regression_count": self.regression_count,
            "not_comparable_count": self.not_comparable_count,
            "recommendation": self.recommendation,
        }
        if self.session_id:
            data["session_id"] = self.session_id
        return data


def build_publish_summary(
    *,
    root: Path,
    from_verify: str | None = None,
    from_session: str | None = None,
) -> PublishSummary:
    """Build a publishable summary from verify or repair-session evidence."""
    if bool(from_verify) == bool(from_session):
        raise ValueError("Provide exactly one of from_verify or from_session.")

    if from_session:
        summary_path = resolve_session_summary_path(root, from_session)
        data = read_json_object(summary_path)
        source_type = "repair_session"
    else:
        summary_path = resolve_path(root, str(from_verify))
        data = read_json_object(summary_path)
        source_type = "verify"

    verdict = str(data.get("verdict") or "unknown")
    summary = PublishSummary(
        source_type=source_type,
        source_path=format_path(summary_path, root),
        verdict=verdict,
        repair_improved=bool(data.get("repair_improved")),
        resolved_count=int_value(data.get("resolved_count")),
        remaining_issue_count=int_value(data.get("remaining_issue_count")),
        new_issue_count=int_value(data.get("new_issue_count")),
        regression_count=int_value(data.get("regression_count")),
        not_comparable_count=int_value(data.get("not_comparable_count")),
        recommendation=recommendation_for_verdict(verdict),
        session_id=optional_string(data.get("session_id")),
    )
    return summary


def render_publish_summary(summary: PublishSummary) -> str:
    """Render Markdown for a GitHub Actions job summary."""
    lines = [
        "# QA-Z Verification Summary",
        "",
        f"- Source: `{summary.source_path}`",
        f"- Source type: `{summary.source_type}`",
        f"- Verdict: {summary.verdict}",
        f"- Recommendation: {summary.recommendation}",
        f"- Resolved: {summary.resolved_count}",
        f"- Remaining: {summary.remaining_issue_count}",
        f"- New issues: {summary.new_issue_count}",
        f"- Regressions: {summary.regression_count}",
        f"- Not comparable: {summary.not_comparable_count}",
    ]
    if summary.session_id:
        lines.insert(3, f"- Session: `{summary.session_id}`")
    return "\n".join(lines) + "\n"


def publish_summary_json(summary: PublishSummary) -> str:
    """Render deterministic JSON for a publish summary."""
    return json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n"


def recommendation_for_verdict(verdict: str) -> str:
    """Return a compact next action for a verification verdict."""
    if verdict == "improved":
        return "merge_candidate"
    if verdict in {"mixed", "regressed", "unchanged", "verification_failed"}:
        return "continue_repair"
    return "inspect_evidence"


def resolve_session_summary_path(root: Path, session: str) -> Path:
    """Resolve a session id, session directory, or summary path."""
    candidate = Path(session).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()

    if candidate.is_file():
        return candidate
    if (candidate / "summary.json").is_file():
        return candidate / "summary.json"
    session_path = root / ".qa-z" / "sessions" / session / "summary.json"
    if session_path.is_file():
        return session_path.resolve()
    raise FileNotFoundError(f"No repair session summary found for {session}.")


def resolve_path(root: Path, value: str) -> Path:
    """Resolve a path relative to the project root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def format_path(path: Path, root: Path) -> str:
    """Return a stable repository-relative path when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise FileNotFoundError(f"Could not read publish source: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Publish source is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError("Publish source JSON must contain an object.")
    return data


def int_value(value: Any) -> int:
    """Return a safe integer from artifact data."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def optional_string(value: Any) -> str | None:
    """Return a non-empty string or None."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None
