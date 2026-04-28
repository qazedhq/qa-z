"""Executor history candidate-input helpers for planning."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.backlog_core import slugify
from qa_z.executor_history_records import executor_history_records
from qa_z.executor_history_summary import (
    dry_run_evidence_summary,
    dry_run_signal_set,
    history_evidence_summary,
    load_or_synthesize_executor_dry_run_summary,
)

__all__ = [
    "discover_executor_history_candidate_inputs",
    "dry_run_evidence_summary",
    "dry_run_signal_set",
    "history_evidence_summary",
    "load_or_synthesize_executor_dry_run_summary",
]


def discover_executor_history_candidate_inputs(root: Path) -> list[dict[str, Any]]:
    """Return normalized backlog candidate packets from executor attempt history."""
    candidates: list[dict[str, Any]] = []
    for record in executor_history_records(root):
        path = record["path"]
        session_id = str(record["session_id"])
        attempts = list(record["attempts"])
        dry_run_path = record["dry_run_path"]
        dry_run = dict(record["dry_run"])
        dry_run_is_fallback = bool(record["dry_run_is_fallback"])
        if not attempts and not dry_run:
            continue
        partial_count = sum(
            1 for item in attempts if str(item.get("result_status") or "") == "partial"
        )
        noop_count = sum(
            1
            for item in attempts
            if str(item.get("result_status") or "") in {"no_op", "not_applicable"}
        )
        rejected_count = sum(
            1
            for item in attempts
            if str(item.get("ingest_status") or "").startswith("rejected_")
        )
        latest = attempts[-1] if attempts else {}
        signal_set = dry_run_signal_set(dry_run)
        dry_run_verdict = str(dry_run.get("verdict") or "").strip()
        evidence = [
            {
                "source": "executor_result_history",
                "path": path,
                "summary": history_evidence_summary(
                    attempt_count=len(attempts),
                    latest_result_status=str(latest.get("result_status") or "unknown"),
                    latest_ingest_status=str(latest.get("ingest_status") or "unknown"),
                    dry_run=dry_run,
                ),
            }
        ]
        if dry_run:
            evidence.append(
                {
                    "source": (
                        "executor_result_dry_run_fallback"
                        if dry_run_is_fallback
                        else "executor_result_dry_run"
                    ),
                    "path": path if dry_run_is_fallback else dry_run_path,
                    "summary": dry_run_evidence_summary(dry_run),
                }
            )
        if partial_count >= 2 or "repeated_partial_attempts" in signal_set:
            signals = ["executor_result_partial", "regression_prevention"]
            if dry_run_verdict == "attention_required":
                signals.append("executor_dry_run_attention")
            candidates.append(
                candidate_packet(
                    session_id=session_id or path.parent.parent.name,
                    category="partial_completion_gap",
                    title_prefix="Inspect repeated partial executor attempts",
                    recommendation="harden_partial_completion_handling",
                    signals=signals,
                    evidence=evidence,
                    impact=4,
                )
            )
        if (
            noop_count >= 2
            or {"repeated_no_op_attempts", "missing_no_op_explanation"} & signal_set
        ):
            signals = ["executor_result_no_op", "regression_prevention"]
            if dry_run_verdict == "attention_required":
                signals.append("executor_dry_run_attention")
            candidates.append(
                candidate_packet(
                    session_id=session_id or path.parent.parent.name,
                    category="no_op_safeguard_gap",
                    title_prefix="Inspect repeated no-op executor attempts",
                    recommendation="harden_executor_no_op_safeguards",
                    signals=signals,
                    evidence=evidence,
                    impact=3,
                )
            )
        if (
            rejected_count >= 2
            or (
                str(latest.get("result_status") or "") == "completed"
                and (
                    str(latest.get("verify_resume_status") or "") == "verify_blocked"
                    or str(latest.get("verification_verdict") or "")
                    in {"mixed", "regressed", "verification_failed"}
                )
            )
            or dry_run_verdict == "blocked"
            or {
                "repeated_rejected_attempts",
                "completed_verify_blocked",
                "scope_validation_failed",
                "validation_conflict",
            }
            & signal_set
        ):
            signals = ["service_readiness_gap", "regression_prevention"]
            if dry_run_verdict == "blocked":
                signals.append("executor_dry_run_blocked")
            elif dry_run_verdict == "attention_required":
                signals.append("executor_dry_run_attention")
            candidates.append(
                candidate_packet(
                    session_id=session_id or path.parent.parent.name,
                    category="workflow_gap",
                    title_prefix="Audit repeated executor attempt friction",
                    recommendation="audit_executor_contract",
                    signals=signals,
                    evidence=evidence,
                    impact=3,
                )
            )
    return candidates


def candidate_packet(
    *,
    session_id: str,
    category: str,
    title_prefix: str,
    recommendation: str,
    signals: list[str],
    evidence: list[dict[str, Any]],
    impact: int,
) -> dict[str, Any]:
    """Build one normalized history-derived candidate input."""
    return {
        "id": f"{category}-{slugify(session_id)}-history",
        "title": f"{title_prefix}: {session_id}",
        "category": category,
        "evidence": [dict(item) for item in evidence],
        "impact": impact,
        "likelihood": 4,
        "confidence": 4,
        "repair_cost": 3,
        "recommendation": recommendation,
        "signals": list(signals),
    }
