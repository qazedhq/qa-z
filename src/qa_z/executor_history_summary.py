"""Executor-history dry-run summary helpers for self-improvement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.executor_dry_run_logic import build_dry_run_summary
from qa_z.self_improvement_runtime import read_json_object

__all__ = [
    "dry_run_evidence_summary",
    "dry_run_signal_set",
    "history_evidence_summary",
    "load_executor_dry_run_summary",
    "load_or_synthesize_executor_dry_run_summary",
]


def load_executor_dry_run_summary(path: Path) -> dict[str, Any]:
    """Load one session dry-run summary when it exists and looks valid."""
    if not path.is_file():
        return {}
    summary = read_json_object(path)
    if summary.get("kind") != "qa_z.executor_result_dry_run":
        return {}
    return {
        **summary,
        "summary_source": summary.get("summary_source") or "materialized",
    }


def load_or_synthesize_executor_dry_run_summary(
    *,
    root: Path,
    history_path: Path,
    summary_path: Path,
    session_id: str,
    attempts: list[dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    """Load a dry-run summary or synthesize one from history when needed."""
    summary = load_executor_dry_run_summary(summary_path)
    if summary:
        return summary, False
    if not attempts:
        return {}, False
    return (
        {
            **build_dry_run_summary(
                session_id=session_id,
                history_path=format_path(history_path, root),
                report_path=format_path(
                    history_path.parent / "dry_run_report.md", root
                ),
                safety_package_id=None,
                attempts=attempts,
            ),
            "summary_source": "history_fallback",
        },
        True,
    )


def dry_run_signal_set(summary: dict[str, Any]) -> set[str]:
    """Return normalized dry-run signal ids."""
    return {
        str(item) for item in summary.get("history_signals", []) if str(item).strip()
    }


def history_evidence_summary(
    *,
    attempt_count: int,
    latest_result_status: str,
    latest_ingest_status: str,
    dry_run: dict[str, Any],
) -> str:
    """Render a compact history evidence summary for self-inspection."""
    parts = [
        f"attempts={attempt_count}",
        f"latest={latest_result_status or 'unknown'}",
        f"latest_ingest={latest_ingest_status or 'unknown'}",
    ]
    if dry_run:
        parts.append(f"dry_run={dry_run.get('verdict') or 'unknown'}")
        parts.append(f"source={dry_run.get('summary_source') or 'unknown'}")
        reason = str(dry_run.get("verdict_reason") or "").strip()
        if reason:
            parts.append(f"reason={reason}")
    return "; ".join(parts)


def dry_run_evidence_summary(summary: dict[str, Any]) -> str:
    """Render one compact dry-run evidence summary for self-inspection."""
    signals = ",".join(dry_run_signal_set(summary)) or "none"
    return (
        f"dry_run={summary.get('verdict') or 'unknown'}; "
        f"source={summary.get('summary_source') or 'unknown'}; "
        f"reason={summary.get('verdict_reason') or 'unknown'}; "
        f"signals={signals}; "
        f"next={summary.get('next_recommendation') or 'inspect executor attempt history'}"
    )
