"""Executor-history record loading helpers for self-improvement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.executor_history_summary import load_or_synthesize_executor_dry_run_summary
from qa_z.self_improvement_runtime import read_json_object

__all__ = [
    "executor_history_records",
]


def executor_history_records(root: Path) -> list[dict[str, Any]]:
    """Return normalized executor-history records for self-inspection policy."""
    sessions_root = root / ".qa-z" / "sessions"
    if not sessions_root.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(sessions_root.glob("*/executor_results/history.json")):
        history = read_json_object(path)
        if history.get("kind") != "qa_z.executor_result_history":
            continue
        session_id = str(history.get("session_id") or path.parent.parent.name).strip()
        attempts = [
            item for item in history.get("attempts", []) if isinstance(item, dict)
        ]
        dry_run_path = path.parent / "dry_run_summary.json"
        dry_run, dry_run_is_fallback = load_or_synthesize_executor_dry_run_summary(
            root=root,
            history_path=path,
            summary_path=dry_run_path,
            session_id=session_id or path.parent.parent.name,
            attempts=attempts,
        )
        records.append(
            {
                "path": path,
                "session_id": session_id or path.parent.parent.name,
                "attempts": attempts,
                "dry_run_path": dry_run_path,
                "dry_run": dry_run,
                "dry_run_is_fallback": dry_run_is_fallback,
            }
        )
    return records
