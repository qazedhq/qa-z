"""Session-scoped executor-result attempt history surface."""

from __future__ import annotations

from typing import Any

from qa_z.executor_history_paths import (
    executor_result_attempts_dir,
    executor_result_dry_run_report_path,
    executor_result_dry_run_summary_path,
    executor_result_history_path,
    executor_results_dir,
)
from qa_z.executor_history_store import (
    append_executor_result_attempt,
    ensure_session_executor_history,
    load_executor_result_history,
)
from qa_z.executor_history_support import (
    allocate_attempt_id,
    legacy_attempt_base,
    resolve_path,
    slugify,
    write_json,
)

EXECUTOR_RESULT_HISTORY_KIND = "qa_z.executor_result_history"
EXECUTOR_RESULT_DRY_RUN_KIND = "qa_z.executor_result_dry_run"
EXECUTOR_RESULT_HISTORY_SCHEMA_VERSION = 1


def executor_result_history_payload(
    *, session_id: str, attempts: list[dict[str, Any]], updated_at: str
) -> dict[str, Any]:
    """Return the stable executor-result history artifact."""
    latest_attempt_id = None
    if attempts:
        latest_attempt_id = str(attempts[-1].get("attempt_id") or "").strip() or None
    return {
        "kind": EXECUTOR_RESULT_HISTORY_KIND,
        "schema_version": EXECUTOR_RESULT_HISTORY_SCHEMA_VERSION,
        "session_id": session_id,
        "updated_at": updated_at,
        "attempt_count": len(attempts),
        "latest_attempt_id": latest_attempt_id,
        "attempts": list(attempts),
    }


__all__ = [
    "EXECUTOR_RESULT_HISTORY_KIND",
    "EXECUTOR_RESULT_DRY_RUN_KIND",
    "EXECUTOR_RESULT_HISTORY_SCHEMA_VERSION",
    "executor_result_history_payload",
    "write_json",
    "allocate_attempt_id",
    "legacy_attempt_base",
    "slugify",
    "resolve_path",
    "executor_results_dir",
    "executor_result_attempts_dir",
    "executor_result_history_path",
    "executor_result_dry_run_summary_path",
    "executor_result_dry_run_report_path",
    "load_executor_result_history",
    "append_executor_result_attempt",
    "ensure_session_executor_history",
]
