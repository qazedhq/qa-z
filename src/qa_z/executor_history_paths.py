"""Path helpers for session-scoped executor-result history."""

from __future__ import annotations

from pathlib import Path


def executor_results_dir(session_dir: Path) -> Path:
    """Return the session-local executor-results directory."""
    return session_dir / "executor_results"


def executor_result_attempts_dir(session_dir: Path) -> Path:
    """Return the attempt artifact directory for a session."""
    return executor_results_dir(session_dir) / "attempts"


def executor_result_history_path(session_dir: Path) -> Path:
    """Return the session-local history artifact path."""
    return executor_results_dir(session_dir) / "history.json"


def executor_result_dry_run_summary_path(session_dir: Path) -> Path:
    """Return the session-local dry-run summary path."""
    return executor_results_dir(session_dir) / "dry_run_summary.json"


def executor_result_dry_run_report_path(session_dir: Path) -> Path:
    """Return the session-local dry-run report path."""
    return executor_results_dir(session_dir) / "dry_run_report.md"
