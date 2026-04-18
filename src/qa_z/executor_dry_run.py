"""Deterministic live-free safety dry-run for executor-result history."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path, resolve_path
from qa_z.executor_history import (
    ensure_session_executor_history,
    executor_result_dry_run_report_path,
    executor_result_dry_run_summary_path,
    executor_result_history_path,
    write_json,
)
from qa_z.executor_dry_run_logic import build_dry_run_summary
from qa_z.executor_safety import executor_safety_package
from qa_z.repair_session import (
    RepairSession,
    ensure_session_safety_artifacts,
    load_repair_session,
)


@dataclass(frozen=True)
class ExecutorDryRunOutcome:
    """Artifacts written by one executor-result dry-run."""

    summary_path: Path
    report_path: Path
    summary: dict[str, Any]


def run_executor_result_dry_run(
    *, root: Path, session_ref: str
) -> ExecutorDryRunOutcome:
    """Evaluate session executor history against the pre-live safety package."""
    session = ensure_session_safety_artifacts(
        load_repair_session(root, session_ref), root
    )
    session_dir = resolve_path(root, session.session_dir)
    history = ensure_session_executor_history(
        root=root,
        session_dir=session_dir,
        session_id=session.session_id,
        updated_at=session.updated_at,
        latest_result_path=session.executor_result_path,
    )
    safety = load_safety_package(root, session)
    summary = dry_run_summary(
        root=root,
        session=session,
        history=history,
        safety=safety,
    )
    summary_path = executor_result_dry_run_summary_path(session_dir)
    report_path = executor_result_dry_run_report_path(session_dir)
    write_json(summary_path, summary)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_dry_run_report(summary), encoding="utf-8")
    return ExecutorDryRunOutcome(
        summary_path=summary_path,
        report_path=report_path,
        summary=summary,
    )


def load_safety_package(root: Path, session: RepairSession) -> dict[str, Any]:
    """Load the session-local safety package or fall back to the static package."""
    path_text = session.safety_artifacts.get("policy_json")
    if not path_text:
        return executor_safety_package()
    path = resolve_path(root, path_text)
    if not path.is_file():
        return executor_safety_package()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return executor_safety_package()
    return loaded


def dry_run_summary(
    *,
    root: Path,
    session: RepairSession,
    history: dict[str, Any],
    safety: dict[str, Any],
) -> dict[str, Any]:
    """Build the dry-run summary payload."""
    attempts = [item for item in history.get("attempts", []) if isinstance(item, dict)]
    return {
        **build_dry_run_summary(
            session_id=session.session_id,
            history_path=format_path(
                executor_result_history_path(resolve_path(root, session.session_dir)),
                root,
            ),
            report_path=format_path(
                executor_result_dry_run_report_path(
                    resolve_path(root, session.session_dir)
                ),
                root,
            ),
            safety_package_id=str(safety.get("package_id") or "").strip() or None,
            attempts=attempts,
        ),
        "summary_source": "materialized",
    }


def render_dry_run_report(summary: dict[str, Any]) -> str:
    """Render the operator-facing dry-run report."""
    lines = [
        "# QA-Z Executor Result Dry-Run",
        "",
        f"- Session: `{summary['session_id']}`",
        f"- Source: `{summary.get('summary_source') or 'unknown'}`",
        f"- Verdict: `{summary['verdict']}`",
        f"- Why: `{summary.get('verdict_reason') or 'history_clear'}`",
        f"- Attempts: `{summary['evaluated_attempt_count']}`",
        f"- Latest attempt: `{summary.get('latest_attempt_id') or 'none'}`",
        f"- Safety package: `{summary.get('safety_package_id') or 'unknown'}`",
        f"- Operator decision: `{summary.get('operator_decision') or 'not recorded'}`",
        f"- Operator summary: {summary.get('operator_summary') or 'not recorded'}",
        f"- Next: {summary['next_recommendation']}",
        (
            "- Rule counts: "
            f"clear={summary.get('rule_status_counts', {}).get('clear', 0)}, "
            f"attention={summary.get('rule_status_counts', {}).get('attention', 0)}, "
            f"blocked={summary.get('rule_status_counts', {}).get('blocked', 0)}"
        ),
        "",
        "## History Signals",
        "",
    ]
    signals = summary.get("history_signals", [])
    if not signals:
        lines.append("- none")
    else:
        for signal in signals:
            lines.append(f"- `{signal}`")
    lines.extend(["", "## Recommended Actions", ""])
    actions = normalize_recommended_actions(summary.get("recommended_actions"))
    if not actions:
        lines.append("- none")
    else:
        for action in actions:
            lines.append(f"- `{action['id']}`: {action['summary']}")
    lines.extend(["", "## Rule Evaluations", ""])
    for rule in summary.get("rule_evaluations", []):
        if not isinstance(rule, dict):
            continue
        lines.append(
            f"- `{rule.get('id', 'unknown')}` -> `{rule.get('status', 'clear')}`: {rule.get('summary', '').strip()}"
        )
    return "\n".join(lines).strip() + "\n"


def normalize_recommended_actions(value: object) -> list[dict[str, str]]:
    """Return recommended action objects from optional dry-run payload data."""
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
