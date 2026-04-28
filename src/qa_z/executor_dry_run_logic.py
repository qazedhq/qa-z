"""Pure logic for live-free executor-result dry-run summaries."""

from __future__ import annotations

from typing import Any

from qa_z.executor_history import (
    EXECUTOR_RESULT_DRY_RUN_KIND,
    EXECUTOR_RESULT_HISTORY_SCHEMA_VERSION,
)
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS

DRY_RUN_ONLY_RULE_IDS = ("executor_history_recorded",)

DRY_RUN_RULE_IDS = DRY_RUN_ONLY_RULE_IDS + EXECUTOR_SAFETY_RULE_IDS


def build_dry_run_summary(
    *,
    session_id: str,
    history_path: str,
    report_path: str,
    safety_package_id: str | None,
    attempts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a dry-run summary payload from session-local attempt history."""
    latest = attempts[-1] if attempts else {}
    signals = history_signals(attempts)
    rule_evaluations = evaluate_rules(attempts, latest)
    verdict = verdict_for_signals(signals)
    actions = recommended_actions(verdict, signals)
    decision = operator_decision(verdict, signals)
    return {
        "kind": EXECUTOR_RESULT_DRY_RUN_KIND,
        "schema_version": EXECUTOR_RESULT_HISTORY_SCHEMA_VERSION,
        "session_id": session_id,
        "history_path": history_path,
        "safety_package_id": safety_package_id,
        "evaluated_attempt_count": len(attempts),
        "latest_attempt_id": latest.get("attempt_id"),
        "latest_result_status": latest.get("result_status"),
        "latest_ingest_status": latest.get("ingest_status"),
        "verdict": verdict,
        "verdict_reason": verdict_reason_for_signals(signals),
        "history_signals": signals,
        "operator_decision": decision,
        "operator_summary": operator_summary(verdict, signals),
        "recommended_actions": actions,
        "rule_status_counts": rule_status_counts(rule_evaluations),
        "rule_evaluations": rule_evaluations,
        "next_recommendation": next_recommendation(verdict, signals),
        "report_path": report_path,
    }


def history_signals(attempts: list[dict[str, Any]]) -> list[str]:
    """Return deterministic history-level dry-run signals."""
    if not attempts:
        return ["no_recorded_attempts"]
    partial_count = sum(
        1 for item in attempts if item.get("result_status") == "partial"
    )
    rejected_count = sum(
        1
        for item in attempts
        if str(item.get("ingest_status") or "").startswith("rejected_")
    )
    noop_count = sum(
        1
        for item in attempts
        if item.get("result_status") in {"no_op", "not_applicable"}
    )
    latest = attempts[-1]
    signals: list[str] = []
    if partial_count >= 2:
        signals.append("repeated_partial_attempts")
    if rejected_count >= 2:
        signals.append("repeated_rejected_attempts")
    if noop_count >= 2:
        signals.append("repeated_no_op_attempts")
    if latest.get("result_status") == "completed" and (
        latest.get("verify_resume_status") == "verify_blocked"
        or latest.get("verification_verdict")
        in {"mixed", "regressed", "verification_failed"}
    ):
        signals.append("completed_verify_blocked")
    if any(
        item.get("provenance_reason") == "scope_validation_failed" for item in attempts
    ):
        signals.append("scope_validation_failed")
    warning_ids = {
        str(warning)
        for item in attempts
        for warning in item.get("warning_ids", [])
        if str(warning).strip()
    }
    if {
        "validation_summary_conflicts_with_results",
        "completed_validation_failed",
    } & warning_ids:
        signals.append("validation_conflict")
    if {
        "no_op_without_explanation",
        "not_applicable_without_explanation",
    } & warning_ids:
        signals.append("missing_no_op_explanation")
    return signals


def evaluate_rules(
    attempts: list[dict[str, Any]], latest: dict[str, Any]
) -> list[dict[str, str]]:
    """Translate history into rule-level dry-run statuses."""
    signals = set(history_signals(attempts))
    return [
        {
            "id": "executor_history_recorded",
            "status": "attention" if "no_recorded_attempts" in signals else "clear",
            "summary": (
                "Executor history contains at least one recorded attempt."
                if "no_recorded_attempts" not in signals
                else (
                    "No executor attempts are recorded; ingest a result before "
                    "relying on dry-run safety evidence."
                )
            ),
        },
        {
            "id": "no_op_requires_explanation",
            "status": "attention"
            if "missing_no_op_explanation" in signals
            else "clear",
            "summary": (
                "No-op and not-applicable attempts carry explanations."
                if "missing_no_op_explanation" not in signals
                else "At least one no-op style attempt lacks an explanation."
            ),
        },
        {
            "id": "retry_boundary_is_manual",
            "status": "attention"
            if {
                "repeated_partial_attempts",
                "repeated_rejected_attempts",
                "repeated_no_op_attempts",
            }
            & signals
            else "clear",
            "summary": (
                "History does not currently show repeated retry pressure."
                if not {
                    "repeated_partial_attempts",
                    "repeated_rejected_attempts",
                    "repeated_no_op_attempts",
                }
                & signals
                else "Repeated attempts need explicit manual review before another retry."
            ),
        },
        {
            "id": "mutation_scope_limited",
            "status": "blocked" if "scope_validation_failed" in signals else "clear",
            "summary": (
                "No recorded scope drift was observed."
                if "scope_validation_failed" not in signals
                else "At least one attempt failed scope validation."
            ),
        },
        {
            "id": "unrelated_refactors_prohibited",
            "status": "clear",
            "summary": "No explicit unrelated-refactor signal was recorded in session history.",
        },
        {
            "id": "verification_required_for_completed",
            "status": "blocked" if "completed_verify_blocked" in signals else "clear",
            "summary": (
                "Completed attempts reached deterministic verification cleanly."
                if "completed_verify_blocked" not in signals
                else "A completed attempt remains blocked or unresolved by verification evidence."
            ),
        },
        {
            "id": "outcome_classification_must_be_honest",
            "status": "attention" if "validation_conflict" in signals else "clear",
            "summary": (
                "No classification conflict was observed in recorded attempts."
                if "validation_conflict" not in signals
                else "Recorded attempts contain validation or completion conflicts."
            ),
        },
    ]


def verdict_for_signals(signals: list[str]) -> str:
    """Return the top-level dry-run verdict."""
    blocked = {"scope_validation_failed", "completed_verify_blocked"}
    if blocked & set(signals):
        return "blocked"
    if signals and signals != ["no_recorded_attempts"]:
        return "attention_required"
    if signals == ["no_recorded_attempts"]:
        return "attention_required"
    return "clear"


def verdict_reason_for_signals(signals: list[str]) -> str:
    """Return a stable machine-readable explanation for the verdict."""
    signal_set = set(signals)
    if "scope_validation_failed" in signal_set:
        return "scope_validation_failed"
    if "completed_verify_blocked" in signal_set:
        return "completed_attempt_not_verification_clean"
    if "validation_conflict" in signal_set:
        return "classification_conflict_requires_review"
    if "missing_no_op_explanation" in signal_set:
        return "no_op_explanation_missing"
    if {
        "repeated_partial_attempts",
        "repeated_rejected_attempts",
        "repeated_no_op_attempts",
    } & signal_set:
        return "manual_retry_review_required"
    if "no_recorded_attempts" in signal_set:
        return "no_recorded_attempts"
    return "history_clear"


def rule_status_counts(rule_evaluations: list[dict[str, str]]) -> dict[str, int]:
    """Return counts for clear, attention, and blocked dry-run rules."""
    counts = {"clear": 0, "attention": 0, "blocked": 0}
    for item in rule_evaluations:
        status = str(item.get("status") or "").strip()
        if status in counts:
            counts[status] += 1
    return counts


def next_recommendation(verdict: str, signals: list[str]) -> str:
    """Return the next deterministic operator recommendation."""
    signal_set = set(signals)
    if "scope_validation_failed" in signal_set:
        return "inspect executor scope drift before another attempt"
    if "completed_verify_blocked" in signal_set:
        return "resolve verification blocking evidence before another completed attempt"
    if "validation_conflict" in signal_set:
        return "review executor validation conflict before another retry"
    if "missing_no_op_explanation" in signal_set:
        return "require no-op explanation before accepting executor result"
    if "repeated_rejected_attempts" in signal_set:
        return "inspect repeated rejected executor results before another retry"
    if "repeated_partial_attempts" in signal_set:
        return "inspect repeated partial attempts before another retry"
    if "repeated_no_op_attempts" in signal_set:
        return "inspect repeated no-op outcomes before another retry"
    if "no_recorded_attempts" in signal_set:
        return "ingest executor result before relying on dry-run safety evidence"
    if verdict == "attention_required":
        return "inspect executor attempt history before another retry"
    return "no immediate safety concerns"


def mixed_attention_summary(signals: list[str]) -> str | None:
    """Return a combined non-blocking attention summary when useful."""
    signal_set = set(signals)
    if {"scope_validation_failed", "completed_verify_blocked"} & signal_set:
        return None

    labels: list[str] = []
    if "validation_conflict" in signal_set:
        labels.append("validation conflicts")
    if "missing_no_op_explanation" in signal_set:
        labels.append("no-op explanation gaps")
    if {
        "repeated_partial_attempts",
        "repeated_rejected_attempts",
        "repeated_no_op_attempts",
    } & signal_set:
        labels.append("retry pressure")

    if len(labels) < 2:
        return None
    if len(labels) == 2:
        joined = " and ".join(labels)
        review_target = "both"
    else:
        joined = f"{', '.join(labels[:-1])}, and {labels[-1]}"
        review_target = "all"
    return (
        f"Executor history has {joined}; review {review_target} recommended "
        "actions before another retry."
    )


def blocked_attention_residue_summary(signals: list[str]) -> str | None:
    """Return extra blocked-summary context without changing blocked priority."""
    signal_set = set(signals)
    if "completed_verify_blocked" not in signal_set:
        return None

    labels: list[str] = []
    if "validation_conflict" in signal_set:
        labels.append("validation conflicts")
    if "missing_no_op_explanation" in signal_set:
        labels.append("no-op explanation gaps")
    if {
        "repeated_partial_attempts",
        "repeated_rejected_attempts",
        "repeated_no_op_attempts",
    } & signal_set:
        labels.append("retry pressure")
    if not labels:
        return None
    if len(labels) == 1:
        joined = labels[0]
    elif len(labels) == 2:
        joined = " and ".join(labels)
    else:
        joined = f"{', '.join(labels[:-1])}, and {labels[-1]}"
    return (
        "A completed executor attempt is still blocked by verification evidence; "
        f"{joined} still need review before another retry."
    )


def operator_summary(verdict: str, signals: list[str]) -> str:
    """Return a stable one-line operator diagnostic for a dry-run result."""
    signal_set = set(signals)
    if "scope_validation_failed" in signal_set:
        return (
            "Executor history is blocked by scope validation; inspect handoff scope "
            "before another attempt."
        )
    if "completed_verify_blocked" in signal_set:
        blocked_summary = blocked_attention_residue_summary(signals)
        if blocked_summary is not None:
            return blocked_summary
        return "A completed executor attempt is still blocked by verification evidence."
    mixed_summary = mixed_attention_summary(signals)
    if mixed_summary is not None:
        return mixed_summary
    if "validation_conflict" in signal_set:
        return "Executor history has validation conflicts that need manual review."
    if "missing_no_op_explanation" in signal_set:
        return "A no-op style executor result needs an explanation before acceptance."
    if "repeated_rejected_attempts" in signal_set:
        return "Repeated rejected executor results need manual review before another retry."
    if "repeated_partial_attempts" in signal_set:
        return "Repeated partial executor attempts need manual review before another retry."
    if "repeated_no_op_attempts" in signal_set:
        return (
            "Repeated no-op executor attempts need manual review before another retry."
        )
    if "no_recorded_attempts" in signal_set:
        return "No executor attempts are recorded for this session."
    if verdict == "clear":
        return "Executor history is clear under the pre-live safety rules."
    return "Executor history needs manual review before another retry."


def operator_decision(verdict: str, signals: list[str]) -> str:
    """Return the stable primary action id for operator-facing surfaces."""
    actions = recommended_actions(verdict, signals)
    if not actions:
        return "inspect_executor_history"
    return actions[0]["id"]


def recommended_actions(verdict: str, signals: list[str]) -> list[dict[str, str]]:
    """Return deterministic operator action objects in priority order."""
    signal_set = set(signals)
    actions: list[dict[str, str]] = []
    mapping = [
        (
            "scope_validation_failed",
            "inspect_scope_drift",
            "Inspect changed files against the bridge handoff scope before another attempt.",
        ),
        (
            "completed_verify_blocked",
            "resolve_verification_blockers",
            (
                "Review verify/summary.json and repair remaining or regressed blockers "
                "before accepting completion."
            ),
        ),
        (
            "validation_conflict",
            "review_validation_conflict",
            (
                "Compare executor validation claims with deterministic verification "
                "artifacts before retrying."
            ),
        ),
        (
            "missing_no_op_explanation",
            "require_no_op_explanation",
            (
                "Ask the executor to explain the no-op or not-applicable result before "
                "accepting it."
            ),
        ),
        (
            "repeated_rejected_attempts",
            "inspect_rejected_results",
            (
                "Inspect rejected executor-result artifacts and fix freshness, "
                "provenance, or schema errors before retrying."
            ),
        ),
        (
            "repeated_partial_attempts",
            "inspect_partial_attempts",
            (
                "Review unresolved repair targets across repeated partial attempts "
                "before retrying."
            ),
        ),
        (
            "repeated_no_op_attempts",
            "inspect_no_op_pattern",
            "Review repeated no-op outcomes before another executor attempt.",
        ),
        (
            "no_recorded_attempts",
            "ingest_executor_result",
            (
                "Run executor-result ingest for a completed external attempt before "
                "relying on dry-run safety evidence."
            ),
        ),
    ]
    for signal, action_id, summary in mapping:
        if signal in signal_set:
            actions.append({"id": action_id, "summary": summary})
    if actions:
        return actions
    if verdict == "clear":
        return [
            {
                "id": "continue_standard_verification",
                "summary": (
                    "Continue normal verification and review; no immediate dry-run "
                    "safety concern is recorded."
                ),
            }
        ]
    return [
        {
            "id": "inspect_executor_history",
            "summary": "Inspect executor attempt history before another retry.",
        }
    ]
