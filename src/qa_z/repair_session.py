"""Local repair-session workflow for QA-Z."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qa_z.adapters.claude import render_claude_handoff
from qa_z.adapters.codex import render_codex_handoff
from qa_z.artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    format_path,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_run_source,
)
from qa_z.repair_handoff import build_repair_handoff, write_repair_handoff_artifact
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.repair_prompt import build_repair_packet, write_repair_artifacts
from qa_z.verification import (
    VerificationComparison,
    compare_verification_runs,
    load_verification_run,
    write_verification_artifacts,
)

REPAIR_SESSION_KIND = "qa_z.repair_session"
REPAIR_SESSION_SUMMARY_KIND = "qa_z.repair_session_summary"
REPAIR_SESSION_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RepairSession:
    """Stable manifest for one local repair session."""

    session_id: str
    state: str
    baseline_run: str
    session_dir: str
    handoff_dir: str
    executor_guide_path: str
    created_at: str
    updated_at: str
    candidate_run: str | None = None
    verify_summary_path: str | None = None
    verify_compare_path: str | None = None
    verify_report_path: str | None = None
    outcome_path: str | None = None
    verdict: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Render the session manifest as JSON-safe data."""
        return {
            "kind": REPAIR_SESSION_KIND,
            "schema_version": REPAIR_SESSION_SCHEMA_VERSION,
            "session_id": self.session_id,
            "state": self.state,
            "baseline_run": self.baseline_run,
            "candidate_run": self.candidate_run,
            "session_dir": self.session_dir,
            "handoff_dir": self.handoff_dir,
            "executor_guide_path": self.executor_guide_path,
            "verify_summary_path": self.verify_summary_path,
            "verify_compare_path": self.verify_compare_path,
            "verify_report_path": self.verify_report_path,
            "outcome_path": self.outcome_path,
            "verdict": self.verdict,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepairSession":
        """Load a repair session from manifest JSON."""
        return cls(
            session_id=str(data["session_id"]),
            state=str(data["state"]),
            baseline_run=str(data["baseline_run"]),
            session_dir=str(data["session_dir"]),
            handoff_dir=str(data["handoff_dir"]),
            executor_guide_path=str(data["executor_guide_path"]),
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            candidate_run=optional_string(data.get("candidate_run")),
            verify_summary_path=optional_string(data.get("verify_summary_path")),
            verify_compare_path=optional_string(data.get("verify_compare_path")),
            verify_report_path=optional_string(data.get("verify_report_path")),
            outcome_path=optional_string(data.get("outcome_path")),
            verdict=optional_string(data.get("verdict")),
        )


@dataclass(frozen=True)
class RepairSessionStartResult:
    """Result returned after creating a repair session."""

    session: RepairSession
    manifest_path: Path


@dataclass(frozen=True)
class RepairSessionVerifyResult:
    """Result returned after verifying a repair session."""

    session: RepairSession
    comparison: VerificationComparison
    summary_path: Path
    outcome_path: Path


def create_repair_session(
    *,
    root: Path,
    config: dict[str, Any],
    baseline_run: str,
    session_id: str | None = None,
    now: str | None = None,
) -> RepairSessionStartResult:
    """Create a local repair session from baseline run evidence."""
    root = root.resolve()
    source = resolve_run_source(root, config, baseline_run)
    summary = load_run_summary(source.summary_path)
    deep_summary = load_sibling_deep_summary(source)
    contract_path = resolve_contract_source(root, config, summary=summary)
    contract = load_contract_context(contract_path, root)
    packet = build_repair_packet(
        summary=summary,
        run_source=source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    handoff = build_repair_handoff(
        repair_packet=packet,
        summary=summary,
        run_source=source,
        root=root,
        deep_summary=deep_summary,
    )

    generated = now or utc_now()
    resolved_session_id = session_id or default_session_id(
        source.run_dir.name, generated
    )
    session_dir = root / ".qa-z" / "sessions" / resolved_session_id
    handoff_dir = session_dir / "handoff"
    session_dir.mkdir(parents=True, exist_ok=True)
    write_repair_artifacts(packet, handoff_dir)
    write_repair_handoff_artifact(handoff, handoff_dir)
    (handoff_dir / "codex.md").write_text(
        render_codex_handoff(handoff), encoding="utf-8"
    )
    (handoff_dir / "claude.md").write_text(
        render_claude_handoff(handoff), encoding="utf-8"
    )

    session = RepairSession(
        session_id=resolved_session_id,
        state="waiting_for_external_repair",
        baseline_run=format_path(source.run_dir, root),
        session_dir=format_path(session_dir, root),
        handoff_dir=format_path(handoff_dir, root),
        executor_guide_path=format_path(session_dir / "executor_guide.md", root),
        created_at=generated,
        updated_at=generated,
    )
    write_executor_guide(root, session)
    manifest_path = write_session_manifest(root, session)
    return RepairSessionStartResult(session=session, manifest_path=manifest_path)


def verify_repair_session(
    *,
    root: Path,
    config: dict[str, Any],
    session_ref: str,
    candidate_run: str,
    now: str | None = None,
) -> RepairSessionVerifyResult:
    """Verify a candidate run against the session baseline and update artifacts."""
    root = root.resolve()
    session = load_repair_session(root, session_ref)
    baseline, _baseline_source = load_verification_run(
        root=root,
        config=config,
        from_run=session.baseline_run,
    )
    candidate, _candidate_source = load_verification_run(
        root=root,
        config=config,
        from_run=candidate_run,
    )
    comparison = compare_verification_runs(baseline, candidate)
    session_dir = resolve_path(root, session.session_dir)
    verify_dir = session_dir / "verify"
    paths = write_verification_artifacts(comparison, verify_dir)
    generated = now or utc_now()
    updated = replace(
        session,
        state="verification_complete",
        candidate_run=format_path(
            resolve_run_source(root, config, candidate_run).run_dir, root
        ),
        verify_summary_path=format_path(paths.summary_path, root),
        verify_compare_path=format_path(paths.compare_path, root),
        verify_report_path=format_path(paths.report_path, root),
        outcome_path=format_path(session_dir / "outcome.md", root),
        verdict=str(comparison.verdict),
        updated_at=generated,
    )
    summary = session_summary_dict(updated, comparison)
    summary_path = session_dir / "summary.json"
    write_json(summary_path, summary)
    outcome_path = session_dir / "outcome.md"
    outcome_path.write_text(render_session_outcome(summary), encoding="utf-8")
    write_session_manifest(root, updated)
    return RepairSessionVerifyResult(
        session=updated,
        comparison=comparison,
        summary_path=summary_path,
        outcome_path=outcome_path,
    )


def load_repair_session(root: Path, session_ref: str) -> RepairSession:
    """Load a repair session by id, directory, or manifest path."""
    manifest_path = resolve_session_manifest_path(root.resolve(), session_ref)
    data = read_json_object(manifest_path)
    if data.get("kind") != REPAIR_SESSION_KIND:
        raise ArtifactLoadError(f"Not a repair session manifest: {manifest_path}")
    return RepairSession.from_dict(data)


def render_session_status(session: RepairSession) -> str:
    """Render human-readable repair-session status."""
    lines = [
        f"Repair session: {session.session_id}",
        f"State: {session.state}",
        f"Baseline run: {session.baseline_run}",
        f"Candidate run: {session.candidate_run or 'none'}",
        f"Handoff: {session.handoff_dir}",
        f"Guide: {session.executor_guide_path}",
        f"Verdict: {session.verdict or 'none'}",
    ]
    return "\n".join(lines)


def session_status_json(session: RepairSession) -> str:
    """Render repair-session status as JSON."""
    return json.dumps(session.to_dict(), indent=2, sort_keys=True) + "\n"


def write_executor_guide(root: Path, session: RepairSession) -> Path:
    """Write a local repair-session guide."""
    path = resolve_path(root, session.executor_guide_path)
    lines = [
        "# QA-Z Repair Session Guide",
        "",
        "This session packages deterministic QA-Z evidence for a local repair workflow.",
        "It does not call live models, dispatch remote work, or edit source code.",
        "",
        "## Inputs",
        "",
        f"- Baseline run: `{session.baseline_run}`",
        f"- Handoff directory: `{session.handoff_dir}`",
        "",
        "## Return Path",
        "",
        "After repair work produces a candidate run, verify it with:",
        "",
        (
            "`python -m qa_z repair-session verify --session "
            f"{session.session_id} --candidate-run <candidate-run>`"
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_session_manifest(root: Path, session: RepairSession) -> Path:
    """Write the session manifest."""
    path = resolve_path(root, session.session_dir) / "session.json"
    write_json(path, session.to_dict())
    return path


def session_summary_dict(
    session: RepairSession, comparison: VerificationComparison
) -> dict[str, Any]:
    """Return a compact repair-session summary from a verification comparison."""
    data = comparison.to_dict()
    summary = data["summary"]
    return {
        "kind": REPAIR_SESSION_SUMMARY_KIND,
        "schema_version": REPAIR_SESSION_SCHEMA_VERSION,
        "session_id": session.session_id,
        "state": session.state,
        "baseline_run": session.baseline_run,
        "candidate_run": session.candidate_run,
        "verdict": str(comparison.verdict),
        "repair_improved": comparison.verdict == "improved",
        "blocking_before": summary["blocking_before"],
        "blocking_after": summary["blocking_after"],
        "resolved_count": summary["resolved_count"],
        "remaining_issue_count": summary["still_failing_count"],
        "new_issue_count": summary["new_issue_count"],
        "regression_count": summary["regression_count"],
        "not_comparable_count": summary["not_comparable_count"],
        "verify_summary_path": session.verify_summary_path,
        "verify_compare_path": session.verify_compare_path,
        "verify_report_path": session.verify_report_path,
    }


def render_session_outcome(summary: dict[str, Any]) -> str:
    """Render a Markdown session outcome."""
    lines = [
        "# QA-Z Repair Session Outcome",
        "",
        f"- Session: `{summary['session_id']}`",
        f"- State: `{summary['state']}`",
        f"- Verdict: `{summary['verdict']}`",
        f"- Repair improved: `{str(summary['repair_improved']).lower()}`",
        f"- Resolved: `{summary['resolved_count']}`",
        f"- Remaining: `{summary['remaining_issue_count']}`",
        f"- New issues: `{summary['new_issue_count']}`",
        f"- Regressions: `{summary['regression_count']}`",
        "",
    ]
    return "\n".join(lines)


def repair_session_exit_code(verdict: str) -> int:
    """Return CLI exit code for a verification verdict."""
    if verdict == "improved":
        return 0
    if verdict == "verification_failed":
        return 2
    return 1


def resolve_session_manifest_path(root: Path, session_ref: str) -> Path:
    """Resolve a session id, directory, or manifest path."""
    candidate = Path(session_ref).expanduser()
    if not candidate.is_absolute():
        direct = root / candidate
        by_id = root / ".qa-z" / "sessions" / session_ref
        if (by_id / "session.json").is_file():
            candidate = by_id
        else:
            candidate = direct
    if candidate.is_dir():
        return candidate / "session.json"
    return candidate


def resolve_path(root: Path, value: str) -> Path:
    """Resolve a path relative to the repository root."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactSourceNotFound(f"Could not read repair session: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"Repair session JSON is invalid: {path}") from exc
    return data if isinstance(data, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write stable JSON with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def default_session_id(run_id: str, generated_at: str) -> str:
    """Return a stable default session id."""
    safe_run = slugify(run_id)
    digits = re.sub(r"\D", "", generated_at)[:14] or "local"
    return f"session-{safe_run}-{digits}"


def slugify(value: str) -> str:
    """Render a stable identifier fragment."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "item"


def optional_string(value: object) -> str | None:
    """Return a string or None for optional manifest fields."""
    if value is None:
        return None
    text = str(value)
    return text if text else None


def utc_now() -> str:
    """Return a UTC timestamp."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
