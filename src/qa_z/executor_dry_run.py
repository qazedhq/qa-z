"""Deterministic live-free safety dry-run for executor-result history."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qa_z.artifacts import resolve_path
from qa_z.executor_dry_run_render import (
    normalize_recommended_actions,
    render_dry_run_report,
)
from qa_z.executor_dry_run_summary import dry_run_summary, load_safety_package
from qa_z.executor_history import ensure_session_executor_history
from qa_z.executor_history_paths import (
    executor_result_dry_run_report_path,
    executor_result_dry_run_summary_path,
)
from qa_z.executor_history_support import write_json
from qa_z.repair_session import load_repair_session
from qa_z.repair_session_support import ensure_session_safety_artifacts

__all__ = [
    "ExecutorDryRunOutcome",
    "run_executor_result_dry_run",
    "load_safety_package",
    "dry_run_summary",
    "render_dry_run_report",
    "normalize_recommended_actions",
]


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
