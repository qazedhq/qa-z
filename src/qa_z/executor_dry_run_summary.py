"""Summary-building helpers for executor dry-run surfaces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path, resolve_path
from qa_z.executor_dry_run_logic import build_dry_run_summary
from qa_z.executor_history_paths import (
    executor_result_dry_run_report_path,
    executor_result_history_path,
)
from qa_z.executor_safety import executor_safety_package
from qa_z.repair_session import RepairSession


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
    session_dir = resolve_path(root, session.session_dir)
    return {
        **build_dry_run_summary(
            session_id=session.session_id,
            history_path=format_path(
                executor_result_history_path(session_dir),
                root,
            ),
            report_path=format_path(
                executor_result_dry_run_report_path(session_dir),
                root,
            ),
            safety_package_id=str(safety.get("package_id") or "").strip() or None,
            attempts=attempts,
        ),
        "summary_source": "materialized",
    }
