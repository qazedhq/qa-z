"""Light repair-session orchestration artifacts."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from qa_z.adapters.claude import render_claude_handoff
from qa_z.adapters.codex import render_codex_handoff
from qa_z.artifacts import (
    ArtifactLoadError,
    format_path,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_path,
    resolve_run_source,
)
from qa_z.repair_handoff import (
    RepairHandoffPacket,
    build_repair_handoff,
    write_repair_handoff_artifact,
)
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.repair_prompt import build_repair_packet, write_repair_artifacts
from qa_z.executor_dry_run_logic import (
    build_dry_run_summary,
    operator_decision as dry_run_operator_decision,
    operator_summary as dry_run_operator_summary,
    recommended_actions as dry_run_recommended_actions_for_signals,
)
from qa_z.executor_history import (
    executor_result_dry_run_report_path,
    executor_result_history_path,
    load_executor_result_history,
)
from qa_z.executor_safety import write_executor_safety_artifacts
from qa_z.verification import VerificationArtifactPaths, VerificationComparison

REPAIR_SESSION_KIND = "qa_z.repair_session"
REPAIR_SESSION_SUMMARY_KIND = "qa_z.repair_session_summary"
REPAIR_SESSION_SCHEMA_VERSION = 1

RepairSessionState = Literal[
    "created",
    "handoff_ready",
    "waiting_for_external_repair",
    "candidate_generated",
    "verification_complete",
    "completed",
    "failed",
]
REPAIR_SESSION_STATES = (
    "created",
    "handoff_ready",
    "waiting_for_external_repair",
    "candidate_generated",
    "verification_complete",
    "completed",
    "failed",
)


@dataclass(frozen=True)
class RepairSession:
    """Persisted state for one local repair workflow."""

    session_id: str
    session_dir: str
    baseline_run_dir: str
    handoff_dir: str
    executor_guide_path: str
    state: RepairSessionState
    created_at: str
    updated_at: str
    baseline_fast_summary_path: str
    handoff_artifacts: dict[str, str] = field(default_factory=dict)
    candidate_run_dir: str | None = None
    verify_dir: str | None = None
    verify_artifacts: dict[str, str] = field(default_factory=dict)
    outcome_path: str | None = None
    summary_path: str | None = None
    baseline_deep_summary_path: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)
    safety_artifacts: dict[str, str] = field(default_factory=dict)
    executor_result_path: str | None = None
    executor_result_status: str | None = None
    executor_result_validation_status: str | None = None
    executor_result_bridge_id: str | None = None
    schema_version: int = REPAIR_SESSION_SCHEMA_VERSION
    kind: str = REPAIR_SESSION_KIND

    def to_dict(self) -> dict[str, Any]:
        """Render the session manifest as deterministic JSON-safe data."""
        return {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "baseline_run_dir": self.baseline_run_dir,
            "baseline_fast_summary_path": self.baseline_fast_summary_path,
            "baseline_deep_summary_path": self.baseline_deep_summary_path,
            "handoff_dir": self.handoff_dir,
            "handoff_artifacts": dict(self.handoff_artifacts),
            "executor_guide_path": self.executor_guide_path,
            "candidate_run_dir": self.candidate_run_dir,
            "verify_dir": self.verify_dir,
            "verify_artifacts": dict(self.verify_artifacts),
            "outcome_path": self.outcome_path,
            "summary_path": self.summary_path,
            "provenance": dict(self.provenance),
            "safety_artifacts": dict(self.safety_artifacts),
            "executor_result_path": self.executor_result_path,
            "executor_result_status": self.executor_result_status,
            "executor_result_validation_status": self.executor_result_validation_status,
            "executor_result_bridge_id": self.executor_result_bridge_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepairSession":
        """Load and validate a repair-session manifest."""
        if data.get("kind") != REPAIR_SESSION_KIND:
            raise ArtifactLoadError("Repair session manifest has an unsupported kind.")
        if int(data.get("schema_version", 0)) != REPAIR_SESSION_SCHEMA_VERSION:
            raise ArtifactLoadError(
                "Repair session manifest has an unsupported schema version."
            )
        required = (
            "session_id",
            "session_dir",
            "baseline_run_dir",
            "handoff_dir",
            "executor_guide_path",
            "state",
            "created_at",
            "updated_at",
            "baseline_fast_summary_path",
        )
        missing = [key for key in required if not data.get(key)]
        if missing:
            raise ArtifactLoadError(
                f"Repair session manifest is missing required fields: {missing}"
            )
        state = str(data["state"])
        if state not in REPAIR_SESSION_STATES:
            raise ArtifactLoadError(f"Unsupported repair session state: {state}")
        return cls(
            session_id=str(data["session_id"]),
            session_dir=str(data["session_dir"]),
            baseline_run_dir=str(data["baseline_run_dir"]),
            handoff_dir=str(data["handoff_dir"]),
            executor_guide_path=str(data["executor_guide_path"]),
            state=state,  # type: ignore[arg-type]
            created_at=str(data["created_at"]),
            updated_at=str(data["updated_at"]),
            baseline_fast_summary_path=str(data["baseline_fast_summary_path"]),
            handoff_artifacts=string_mapping(data.get("handoff_artifacts", {})),
            candidate_run_dir=optional_string(data.get("candidate_run_dir")),
            verify_dir=optional_string(data.get("verify_dir")),
            verify_artifacts=string_mapping(data.get("verify_artifacts", {})),
            outcome_path=optional_string(data.get("outcome_path")),
            summary_path=optional_string(data.get("summary_path")),
            baseline_deep_summary_path=optional_string(
                data.get("baseline_deep_summary_path")
            ),
            provenance=dict(data["provenance"])
            if isinstance(data.get("provenance"), dict)
            else {},
            safety_artifacts=string_mapping(data.get("safety_artifacts", {})),
            executor_result_path=optional_string(data.get("executor_result_path")),
            executor_result_status=optional_string(data.get("executor_result_status")),
            executor_result_validation_status=optional_string(
                data.get("executor_result_validation_status")
            ),
            executor_result_bridge_id=optional_string(
                data.get("executor_result_bridge_id")
            ),
        )


@dataclass(frozen=True)
class RepairSessionStartResult:
    """Artifacts created by repair-session start."""

    session: RepairSession
    handoff: RepairHandoffPacket


def create_repair_session(
    *,
    root: Path,
    config: dict[str, Any],
    baseline_run: str,
    session_id: str | None = None,
) -> RepairSessionStartResult:
    """Create a repair session from an existing baseline run."""
    baseline_source = resolve_run_source(root, config, baseline_run)
    summary = load_run_summary(baseline_source.summary_path)
    deep_summary = load_sibling_deep_summary(baseline_source)
    contract_path = resolve_contract_source(root, config, summary=summary)
    contract = load_contract_context(contract_path, root)
    repair_packet = build_repair_packet(
        summary=summary,
        run_source=baseline_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    handoff = build_repair_handoff(
        repair_packet=repair_packet,
        summary=summary,
        run_source=baseline_source,
        root=root,
        deep_summary=deep_summary,
    )

    resolved_session_id = normalize_session_id(session_id or create_session_id())
    session_dir = sessions_dir(root) / resolved_session_id
    manifest_path = session_dir / "session.json"
    if manifest_path.exists():
        raise ValueError(
            f"Repair session already exists: {format_path(session_dir, root)}"
        )

    handoff_dir = session_dir / "handoff"
    write_repair_artifacts(repair_packet, handoff_dir)
    write_repair_handoff_artifact(handoff, handoff_dir)
    (handoff_dir / "codex.md").write_text(
        render_codex_handoff(handoff), encoding="utf-8"
    )
    (handoff_dir / "claude.md").write_text(
        render_claude_handoff(handoff), encoding="utf-8"
    )
    safety_artifacts = write_executor_safety_artifacts(
        root=root, output_dir=session_dir
    )

    now = utc_now()
    session = RepairSession(
        session_id=resolved_session_id,
        session_dir=format_path(session_dir, root),
        baseline_run_dir=format_path(baseline_source.run_dir, root),
        baseline_fast_summary_path=format_path(baseline_source.summary_path, root),
        baseline_deep_summary_path=(
            format_path(baseline_source.run_dir / "deep" / "summary.json", root)
            if deep_summary is not None
            else None
        ),
        handoff_dir=format_path(handoff_dir, root),
        handoff_artifacts=handoff_artifact_paths(handoff_dir, root),
        executor_guide_path=format_path(session_dir / "executor_guide.md", root),
        state="waiting_for_external_repair",
        created_at=now,
        updated_at=now,
        provenance={
            "baseline_status": summary.status,
            "contract_path": summary.contract_path,
            "repair_needed": repair_packet.repair_needed,
        },
        safety_artifacts=safety_artifacts,
    )
    write_executor_guide(session, handoff, root)
    write_session_manifest(session, root)
    return RepairSessionStartResult(session=session, handoff=handoff)


def complete_session_verification(
    *,
    session: RepairSession,
    root: Path,
    candidate_run_dir: Path,
    verify_paths: VerificationArtifactPaths,
    comparison: VerificationComparison,
) -> tuple[RepairSession, dict[str, Any]]:
    """Write final session outcome artifacts and update the manifest."""
    session_dir = resolve_path(root, session.session_dir)
    summary_path = session_dir / "summary.json"
    outcome_path = session_dir / "outcome.md"
    updated = replace(
        session,
        state="completed",
        updated_at=utc_now(),
        candidate_run_dir=format_path(candidate_run_dir, root),
        verify_dir=format_path(verify_paths.summary_path.parent, root),
        verify_artifacts={
            "summary_json": format_path(verify_paths.summary_path, root),
            "compare_json": format_path(verify_paths.compare_path, root),
            "report_markdown": format_path(verify_paths.report_path, root),
        },
        outcome_path=format_path(outcome_path, root),
        summary_path=format_path(summary_path, root),
    )
    dry_run_summary = load_session_dry_run_summary(updated, root)
    summary = session_summary_dict(updated, comparison, dry_run_summary=dry_run_summary)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    outcome_path.write_text(
        render_outcome_markdown(updated, comparison, summary), encoding="utf-8"
    )
    write_session_manifest(updated, root)
    return updated, summary


def load_repair_session(root: Path, session: str) -> RepairSession:
    """Load a repair-session manifest by id, directory, or session.json path."""
    session_dir = resolve_session_dir(root, session)
    manifest_path = session_dir / "session.json"
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactLoadError(
            f"Could not read repair session: {manifest_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(
            f"Repair session manifest is not valid JSON: {manifest_path}"
        ) from exc
    if not isinstance(data, dict):
        raise ArtifactLoadError("Repair session manifest must contain an object.")
    return RepairSession.from_dict(data)


def write_session_manifest(session: RepairSession, root: Path) -> Path:
    """Persist a repair-session manifest."""
    session_dir = resolve_path(root, session.session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)
    path = session_dir / "session.json"
    path.write_text(
        json.dumps(session.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def ensure_session_safety_artifacts(
    session: RepairSession, root: Path
) -> RepairSession:
    """Backfill session safety artifacts for manifests created before P9."""
    json_path_text = session.safety_artifacts.get("policy_json")
    markdown_path_text = session.safety_artifacts.get("policy_markdown")
    if json_path_text and markdown_path_text:
        json_path = resolve_path(root, json_path_text)
        markdown_path = resolve_path(root, markdown_path_text)
        if json_path.is_file() and markdown_path.is_file():
            return session

    session_dir = resolve_path(root, session.session_dir)
    updated = replace(
        session,
        safety_artifacts=write_executor_safety_artifacts(
            root=root, output_dir=session_dir
        ),
        updated_at=utc_now(),
    )
    write_session_manifest(updated, root)
    return updated


def write_executor_guide(
    session: RepairSession, handoff: RepairHandoffPacket, root: Path
) -> Path:
    """Write a guide for an external human or agent executor."""
    path = resolve_path(root, session.executor_guide_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_executor_guide(session, handoff), encoding="utf-8")
    return path


def render_executor_guide(session: RepairSession, handoff: RepairHandoffPacket) -> str:
    """Render the external executor guide Markdown."""
    lines = [
        "# QA-Z Repair Session Executor Guide",
        "",
        "This session packages deterministic QA-Z evidence for an external repair executor.",
        "It does not call Codex or Claude APIs, run remote jobs, schedule work, or edit code by itself.",
        "",
        "## Session",
        "",
        f"- Session id: `{session.session_id}`",
        f"- State: `{session.state}`",
        f"- Baseline run: `{session.baseline_run_dir}`",
        f"- Handoff directory: `{session.handoff_dir}`",
        "",
        "## Handoff Artifacts",
        "",
    ]
    for label, path in session.handoff_artifacts.items():
        lines.append(f"- {label}: `{path}`")
    lines.extend(["", "## Repair Objectives", ""])
    targets = handoff.targets
    if not targets:
        lines.append("- No blocking repair targets were found in the baseline run.")
    for target in targets:
        location = f" at `{target.location}`" if target.location else ""
        lines.append(f"- `{target.id}`{location}: {target.objective}")
    lines.extend(["", "## Do Not Change", ""])
    for item in handoff.non_goals:
        lines.append(f"- {item}")
    lines.extend(
        [
            "- Do not weaken deterministic checks, tests, or configured gates.",
            "",
            "## Pre-Live Safety Package",
            "",
            f"- Policy JSON: `{session.safety_artifacts.get('policy_json', 'none')}`",
            f"- Policy Markdown: `{session.safety_artifacts.get('policy_markdown', 'none')}`",
            "- This package freezes the local executor safety boundary before any live executor work.",
            "",
            "## After Editing",
            "",
            "Run one of these local verification flows from the repository root:",
            "",
            "```bash",
            f"python -m qa_z repair-session verify --session {session.session_dir} --rerun",
            "```",
            "",
            "or, if a candidate run already exists:",
            "",
            "```bash",
            (
                "python -m qa_z repair-session verify "
                f"--session {session.session_dir} "
                "--candidate-run .qa-z/runs/<candidate>"
            ),
            "```",
            "",
            "The verify step writes session-local verification artifacts and an outcome summary.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_session_status(session: RepairSession) -> str:
    """Render current session state for human CLI output."""
    return render_session_status_with_dry_run(session, dry_run_summary=None)


def render_session_status_with_dry_run(
    session: RepairSession, *, dry_run_summary: dict[str, Any] | None
) -> str:
    """Render current session state for human CLI output with optional dry-run data."""
    dry_run_line = "Executor dry-run: none"
    dry_run_source_line = "Executor dry-run source: none"
    dry_run_decision_line = "Executor dry-run decision: none"
    dry_run_diagnostic_line = "Executor dry-run diagnostic: none"
    dry_run_action_line = "Executor dry-run action: none"
    if dry_run_summary:
        verdict = str(dry_run_summary.get("verdict") or "unknown")
        reason = str(dry_run_summary.get("verdict_reason") or "").strip()
        source = str(dry_run_summary.get("summary_source") or "").strip() or "unknown"
        decision = str(dry_run_summary.get("operator_decision") or "").strip()
        diagnostic = str(dry_run_summary.get("operator_summary") or "").strip()
        actions = normalized_dry_run_actions(dry_run_summary.get("recommended_actions"))
        dry_run_line = (
            f"Executor dry-run: {verdict} ({reason})"
            if reason
            else f"Executor dry-run: {verdict}"
        )
        dry_run_source_line = f"Executor dry-run source: {source}"
        if decision:
            dry_run_decision_line = f"Executor dry-run decision: {decision}"
        if diagnostic:
            dry_run_diagnostic_line = f"Executor dry-run diagnostic: {diagnostic}"
        if actions:
            dry_run_action_line = f"Executor dry-run action: {actions[0]['summary']}"
    return "\n".join(
        [
            f"qa-z repair-session: {session.state}",
            f"Session: {session.session_dir}",
            f"Baseline run: {session.baseline_run_dir}",
            f"Handoff: {session.handoff_dir}",
            f"Candidate run: {session.candidate_run_dir or 'none'}",
            f"Verify: {session.verify_dir or 'none'}",
            f"Outcome: {session.outcome_path or 'none'}",
            f"Executor result: {session.executor_result_status or 'none'}",
            dry_run_line,
            dry_run_source_line,
            dry_run_decision_line,
            dry_run_diagnostic_line,
            dry_run_action_line,
        ]
    )


def session_status_dict(
    session: RepairSession, *, dry_run_summary: dict[str, Any] | None
) -> dict[str, Any]:
    """Render repair-session status as JSON-safe data with optional dry-run fields."""
    payload = session.to_dict()
    if dry_run_summary:
        payload["executor_dry_run_verdict"] = dry_run_summary.get("verdict")
        payload["executor_dry_run_reason"] = dry_run_summary.get("verdict_reason")
        payload["executor_dry_run_source"] = dry_run_summary.get("summary_source")
        payload["executor_dry_run_attempt_count"] = dry_run_summary.get(
            "evaluated_attempt_count"
        )
        payload["executor_dry_run_history_signals"] = [
            str(item)
            for item in dry_run_summary.get("history_signals", [])
            if str(item).strip()
        ]
        if dry_run_summary.get("operator_decision"):
            payload["executor_dry_run_operator_decision"] = dry_run_summary.get(
                "operator_decision"
            )
        if dry_run_summary.get("operator_summary"):
            payload["executor_dry_run_operator_summary"] = dry_run_summary.get(
                "operator_summary"
            )
        actions = normalized_dry_run_actions(dry_run_summary.get("recommended_actions"))
        if actions:
            payload["executor_dry_run_recommended_actions"] = actions
    return payload


def render_session_start_stdout(session: RepairSession) -> str:
    """Render session creation output."""
    return "\n".join(
        [
            f"qa-z repair-session start: {session.state}",
            f"Session: {session.session_dir}",
            f"Baseline run: {session.baseline_run_dir}",
            f"Handoff: {session.handoff_dir}",
            f"Executor guide: {session.executor_guide_path}",
        ]
    )


def render_session_verify_stdout(
    session: RepairSession, summary: dict[str, Any]
) -> str:
    """Render session verification output."""
    return "\n".join(
        [
            f"qa-z repair-session verify: {summary['verdict']}",
            f"Session: {session.session_dir}",
            f"Candidate run: {session.candidate_run_dir or 'none'}",
            f"Verify: {session.verify_dir or 'none'}",
            f"Outcome: {session.outcome_path or 'none'}",
        ]
    )


def session_summary_json(summary: dict[str, Any]) -> str:
    """Render session summary JSON for stdout."""
    return json.dumps(summary, indent=2, sort_keys=True) + "\n"


def session_summary_dict(
    session: RepairSession,
    comparison: VerificationComparison,
    *,
    dry_run_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the compact top-level session summary."""
    comparison_summary = comparison.summary
    summary = {
        "kind": REPAIR_SESSION_SUMMARY_KIND,
        "schema_version": REPAIR_SESSION_SCHEMA_VERSION,
        "session_id": session.session_id,
        "state": session.state,
        "baseline_run_dir": session.baseline_run_dir,
        "candidate_run_dir": session.candidate_run_dir,
        "verify_dir": session.verify_dir,
        "outcome_path": session.outcome_path,
        "verdict": comparison.verdict,
        "repair_improved": comparison.verdict == "improved",
        "blocking_before": comparison_summary["blocking_before"],
        "blocking_after": comparison_summary["blocking_after"],
        "resolved_count": comparison_summary["resolved_count"],
        "remaining_issue_count": comparison_summary["blocking_after"],
        "new_issue_count": comparison_summary["new_issue_count"],
        "regression_count": comparison_summary["regression_count"],
        "not_comparable_count": comparison_summary["not_comparable_count"],
        "next_recommendation": recommendation_for_verdict(comparison.verdict),
    }
    if dry_run_summary:
        summary["executor_dry_run_verdict"] = dry_run_summary.get("verdict")
        summary["executor_dry_run_reason"] = dry_run_summary.get("verdict_reason")
        summary["executor_dry_run_source"] = dry_run_summary.get("summary_source")
        summary["executor_dry_run_attempt_count"] = dry_run_summary.get(
            "evaluated_attempt_count"
        )
        summary["executor_dry_run_history_signals"] = [
            str(item)
            for item in dry_run_summary.get("history_signals", [])
            if str(item).strip()
        ]
        summary["executor_dry_run_next_recommendation"] = dry_run_summary.get(
            "next_recommendation"
        )
        if dry_run_summary.get("operator_decision"):
            summary["executor_dry_run_operator_decision"] = dry_run_summary.get(
                "operator_decision"
            )
        if dry_run_summary.get("operator_summary"):
            summary["executor_dry_run_operator_summary"] = dry_run_summary.get(
                "operator_summary"
            )
        actions = normalized_dry_run_actions(dry_run_summary.get("recommended_actions"))
        if actions:
            summary["executor_dry_run_recommended_actions"] = actions
    return summary


def render_outcome_markdown(
    session: RepairSession,
    comparison: VerificationComparison,
    summary: dict[str, Any],
) -> str:
    """Render a human-readable session outcome."""
    lines = [
        "# QA-Z Repair Session Outcome",
        "",
        f"- Final verdict: `{comparison.verdict}`",
        f"- Next recommendation: {summary['next_recommendation']}",
        f"- Session: `{session.session_dir}`",
        f"- Baseline run: `{session.baseline_run_dir}`",
        f"- Candidate run: `{session.candidate_run_dir or 'none'}`",
        f"- Verify artifacts: `{session.verify_dir or 'none'}`",
        f"- Executor result: `{session.executor_result_status or 'none'}`",
        "",
        "## Counts",
        "",
        f"- Blocking before: {summary['blocking_before']}",
        f"- Blocking after: {summary['blocking_after']}",
        f"- Resolved issues: {summary['resolved_count']}",
        f"- Remaining issues: {summary['remaining_issue_count']}",
        f"- New or regressed issues: {summary['new_issue_count']}",
        f"- Regressions: {summary['regression_count']}",
        f"- Not comparable: {summary['not_comparable_count']}",
        "",
        "## Evidence",
        "",
        f"- Verify summary: `{session.verify_artifacts.get('summary_json', 'none')}`",
        f"- Verify compare: `{session.verify_artifacts.get('compare_json', 'none')}`",
        f"- Verify report: `{session.verify_artifacts.get('report_markdown', 'none')}`",
    ]
    if summary.get("executor_dry_run_verdict"):
        lines.extend(
            [
                "",
                "## Executor Dry-Run",
                "",
                f"- Executor dry-run verdict: `{summary['executor_dry_run_verdict']}`",
                (
                    f"- Dry-run reason: `{summary['executor_dry_run_reason']}`"
                    if summary.get("executor_dry_run_reason")
                    else "- Dry-run reason: `unknown`"
                ),
                (
                    f"- Dry-run source: `{summary['executor_dry_run_source']}`"
                    if summary.get("executor_dry_run_source")
                    else "- Dry-run source: `unknown`"
                ),
                (
                    f"- Dry-run attempts: `{summary['executor_dry_run_attempt_count']}`"
                    if summary.get("executor_dry_run_attempt_count") is not None
                    else "- Dry-run attempts: `unknown`"
                ),
                (
                    "- Dry-run history signals: "
                    + ", ".join(
                        f"`{signal}`"
                        for signal in summary.get(
                            "executor_dry_run_history_signals", []
                        )
                    )
                    if summary.get("executor_dry_run_history_signals")
                    else "- Dry-run history signals: `none`"
                ),
                (
                    "- Dry-run next recommendation: "
                    f"{summary['executor_dry_run_next_recommendation']}"
                ),
            ]
        )
        operator = str(summary.get("executor_dry_run_operator_summary") or "").strip()
        decision = str(summary.get("executor_dry_run_operator_decision") or "").strip()
        if decision:
            lines.append(f"- Dry-run operator decision: `{decision}`")
        if operator:
            lines.append(f"- Dry-run operator summary: {operator}")
        action_text = dry_run_action_summary_text(
            summary.get("executor_dry_run_recommended_actions")
        )
        if action_text:
            lines.append(f"- Dry-run recommended actions: {action_text}")
    return "\n".join(lines).strip() + "\n"


def load_session_dry_run_summary(
    session: RepairSession, root: Path
) -> dict[str, Any] | None:
    """Load a session-local executor dry-run summary when present."""
    session_dir = resolve_path(root, session.session_dir)
    path = session_dir / "executor_results" / "dry_run_summary.json"
    if not path.is_file():
        return synthesize_session_dry_run_summary(session, root)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return synthesize_session_dry_run_summary(session, root)
    if loaded.get("kind") != "qa_z.executor_result_dry_run":
        return synthesize_session_dry_run_summary(session, root)
    return enrich_dry_run_operator_fields({**loaded, "summary_source": "materialized"})


def synthesize_session_dry_run_summary(
    session: RepairSession, root: Path
) -> dict[str, Any] | None:
    """Synthesize dry-run context from session history when no summary exists."""
    session_dir = resolve_path(root, session.session_dir)
    history_path = executor_result_history_path(session_dir)
    if not history_path.is_file():
        return None
    history = load_executor_result_history(history_path, session_id=session.session_id)
    attempts = [item for item in history.get("attempts", []) if isinstance(item, dict)]
    if not attempts:
        return None
    return enrich_dry_run_operator_fields(
        {
            **build_dry_run_summary(
                session_id=session.session_id,
                history_path=format_path(history_path, root),
                report_path=format_path(
                    executor_result_dry_run_report_path(session_dir), root
                ),
                safety_package_id=safety_package_id_for_session(session, root),
                attempts=attempts,
            ),
            "summary_source": "history_fallback",
        }
    )


def safety_package_id_for_session(session: RepairSession, root: Path) -> str | None:
    """Return the session-local safety package id when it can be read."""
    path_text = session.safety_artifacts.get("policy_json")
    if not path_text:
        return None
    path = resolve_path(root, path_text)
    if not path.is_file():
        return None
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return None
    package_id = str(loaded.get("package_id") or "").strip()
    return package_id or None


def recommendation_for_verdict(verdict: str) -> str:
    """Return the deterministic next step for a verification verdict."""
    if verdict == "improved":
        return "merge candidate"
    if verdict == "mixed":
        return "inspect regressions"
    if verdict == "regressed":
        return "reject repair"
    if verdict == "verification_failed":
        return "rerun needed"
    return "continue repair"


def enrich_dry_run_operator_fields(summary: dict[str, Any]) -> dict[str, Any]:
    """Backfill additive operator diagnostic fields for older dry-run summaries."""
    signals = [
        str(item) for item in summary.get("history_signals", []) if str(item).strip()
    ]
    verdict = str(summary.get("verdict") or "").strip()
    enriched = dict(summary)
    if not str(enriched.get("operator_decision") or "").strip():
        enriched["operator_decision"] = dry_run_operator_decision(verdict, signals)
    if not str(enriched.get("operator_summary") or "").strip():
        enriched["operator_summary"] = dry_run_operator_summary(verdict, signals)
    if not normalized_dry_run_actions(enriched.get("recommended_actions")):
        enriched["recommended_actions"] = dry_run_recommended_actions_for_signals(
            verdict,
            signals,
        )
    return enriched


def normalized_dry_run_actions(value: object) -> list[dict[str, str]]:
    """Normalize optional dry-run recommended actions for JSON and Markdown."""
    if not isinstance(value, list):
        return []
    actions: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action_id = str(item.get("id") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if action_id and summary:
            actions.append({"id": action_id, "summary": summary})
    return actions


def dry_run_action_summary_text(value: object) -> str:
    """Render recommended dry-run action summaries as one compact line."""
    return "; ".join(action["summary"] for action in normalized_dry_run_actions(value))


def handoff_artifact_paths(handoff_dir: Path, root: Path) -> dict[str, str]:
    """Return stable handoff artifact paths for the manifest."""
    return {
        "packet_json": format_path(handoff_dir / "packet.json", root),
        "prompt_markdown": format_path(handoff_dir / "prompt.md", root),
        "handoff_json": format_path(handoff_dir / "handoff.json", root),
        "codex_markdown": format_path(handoff_dir / "codex.md", root),
        "claude_markdown": format_path(handoff_dir / "claude.md", root),
    }


def resolve_session_dir(root: Path, session: str) -> Path:
    """Resolve a session id, directory, or session.json file."""
    path = Path(session).expanduser()
    if path.name == "session.json":
        path = path.parent
    elif not path.is_absolute() and len(path.parts) == 1:
        path = sessions_dir(root) / path
    elif not path.is_absolute():
        path = root / path
    return path.resolve()


def sessions_dir(root: Path) -> Path:
    """Return the default local repair-session directory."""
    return (root / ".qa-z" / "sessions").resolve()


def create_session_id() -> str:
    """Create a compact unique repair-session id."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{uuid4().hex[:6]}"


def normalize_session_id(session_id: str) -> str:
    """Validate a session id so it cannot escape the sessions directory."""
    normalized = session_id.strip()
    if not normalized or normalized in {".", ".."}:
        raise ValueError("Repair session id must not be empty.")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", normalized):
        raise ValueError(
            "Repair session id may contain only letters, numbers, dot, underscore, and dash."
        )
    return normalized


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def optional_string(value: object) -> str | None:
    """Return a string value or None."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def string_mapping(value: object) -> dict[str, str]:
    """Return a string-to-string mapping."""
    if not isinstance(value, dict):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if str(key).strip() and item is not None
    }
