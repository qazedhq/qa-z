"""Tests for live-free executor-result dry-run summary logic."""

from __future__ import annotations

from typing import Any

from qa_z.executor_dry_run_logic import (
    DRY_RUN_ONLY_RULE_IDS,
    DRY_RUN_RULE_IDS,
    build_dry_run_summary,
    evaluate_rules,
)
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS, executor_safety_package


def build_summary(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a dry-run summary with compact stable defaults."""
    return build_dry_run_summary(
        session_id="session-one",
        history_path=".qa-z/sessions/session-one/executor_results/history.json",
        report_path=".qa-z/sessions/session-one/executor_results/dry_run_report.md",
        safety_package_id="pre_live_executor_safety_v1",
        attempts=attempts,
    )


def test_dry_run_rule_catalog_matches_evaluated_rule_order() -> None:
    assert tuple(item["id"] for item in evaluate_rules([], {})) == DRY_RUN_RULE_IDS


def test_dry_run_rule_catalog_extends_executor_safety_package_rules() -> None:
    safety_rule_ids = tuple(rule["id"] for rule in executor_safety_package()["rules"])

    assert DRY_RUN_ONLY_RULE_IDS == ("executor_history_recorded",)
    assert safety_rule_ids == EXECUTOR_SAFETY_RULE_IDS
    assert DRY_RUN_RULE_IDS == DRY_RUN_ONLY_RULE_IDS + EXECUTOR_SAFETY_RULE_IDS


def test_build_dry_run_summary_flags_repeated_partial_attempts() -> None:
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "manual_retry_review_required"
    assert summary["history_signals"] == ["repeated_partial_attempts"]
    assert summary["operator_decision"] == "inspect_partial_attempts"
    assert summary["next_recommendation"] == (
        "inspect repeated partial attempts before another retry"
    )
    assert summary["operator_summary"] == (
        "Repeated partial executor attempts need manual review before another retry."
    )
    assert summary["recommended_actions"] == [
        {
            "id": "inspect_partial_attempts",
            "summary": (
                "Review unresolved repair targets across repeated partial attempts "
                "before retrying."
            ),
        }
    ]
    assert summary["rule_status_counts"] == {"clear": 6, "attention": 1, "blocked": 0}


def test_build_dry_run_summary_prioritizes_rejected_results_over_partial_retry_review() -> (
    None
):
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "partial",
                "ingest_status": "rejected_stale",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "result_status": "partial",
                "ingest_status": "rejected_mismatch",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "manual_retry_review_required"
    assert summary["history_signals"] == [
        "repeated_partial_attempts",
        "repeated_rejected_attempts",
    ]
    assert summary["operator_decision"] == "inspect_rejected_results"
    assert summary["next_recommendation"] == (
        "inspect repeated rejected executor results before another retry"
    )
    assert summary["operator_summary"] == (
        "Repeated rejected executor results need manual review before another retry."
    )
    assert [action["id"] for action in summary["recommended_actions"]] == [
        "inspect_rejected_results",
        "inspect_partial_attempts",
    ]
    assert summary["rule_status_counts"] == {"clear": 6, "attention": 1, "blocked": 0}


def test_build_dry_run_summary_blocks_scope_validation_failures() -> None:
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": "scope_validation_failed",
            }
        ]
    )

    assert summary["verdict"] == "blocked"
    assert summary["verdict_reason"] == "scope_validation_failed"
    assert summary["history_signals"] == ["scope_validation_failed"]
    assert summary["operator_decision"] == "inspect_scope_drift"
    assert summary["next_recommendation"] == (
        "inspect executor scope drift before another attempt"
    )
    assert summary["operator_summary"] == (
        "Executor history is blocked by scope validation; inspect handoff scope "
        "before another attempt."
    )
    assert summary["recommended_actions"][0]["id"] == "inspect_scope_drift"
    assert summary["rule_status_counts"] == {"clear": 6, "attention": 0, "blocked": 1}


def test_build_dry_run_summary_prioritizes_validation_conflicts_over_no_op_gaps() -> (
    None
):
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": [
                    "no_op_without_explanation",
                    "validation_summary_conflicts_with_results",
                ],
                "provenance_reason": None,
            }
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "classification_conflict_requires_review"
    assert summary["history_signals"] == [
        "validation_conflict",
        "missing_no_op_explanation",
    ]
    assert summary["operator_decision"] == "review_validation_conflict"
    assert summary["next_recommendation"] == (
        "review executor validation conflict before another retry"
    )
    assert summary["operator_summary"] == (
        "Executor history has validation conflicts and no-op explanation gaps; "
        "review both recommended actions before another retry."
    )
    assert [action["id"] for action in summary["recommended_actions"]] == [
        "review_validation_conflict",
        "require_no_op_explanation",
    ]
    assert summary["rule_status_counts"] == {"clear": 5, "attention": 2, "blocked": 0}


def test_build_dry_run_summary_requires_no_op_explanation_when_missing() -> None:
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": ["no_op_without_explanation"],
                "provenance_reason": None,
            }
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "no_op_explanation_missing"
    assert summary["history_signals"] == ["missing_no_op_explanation"]
    assert summary["operator_decision"] == "require_no_op_explanation"
    assert summary["next_recommendation"] == (
        "require no-op explanation before accepting executor result"
    )
    assert summary["operator_summary"] == (
        "A no-op style executor result needs an explanation before acceptance."
    )
    assert summary["recommended_actions"] == [
        {
            "id": "require_no_op_explanation",
            "summary": (
                "Ask the executor to explain the no-op or not-applicable result "
                "before accepting it."
            ),
        }
    ]
    assert summary["rule_status_counts"] == {"clear": 6, "attention": 1, "blocked": 0}


def test_build_dry_run_summary_guides_repeated_no_op_attempts() -> None:
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "manual_retry_review_required"
    assert summary["history_signals"] == ["repeated_no_op_attempts"]
    assert summary["operator_decision"] == "inspect_no_op_pattern"
    assert summary["next_recommendation"] == (
        "inspect repeated no-op outcomes before another retry"
    )
    assert summary["operator_summary"] == (
        "Repeated no-op executor attempts need manual review before another retry."
    )
    assert summary["recommended_actions"] == [
        {
            "id": "inspect_no_op_pattern",
            "summary": "Review repeated no-op outcomes before another executor attempt.",
        }
    ]
    assert [
        item["id"]
        for item in summary["rule_evaluations"]
        if item["status"] == "attention"
    ] == ["retry_boundary_is_manual"]
    assert summary["rule_status_counts"] == {"clear": 6, "attention": 1, "blocked": 0}


def test_build_dry_run_summary_explains_mixed_attention_signals() -> None:
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": ["no_op_without_explanation"],
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_skipped",
                "verification_verdict": None,
                "warning_ids": ["validation_summary_conflicts_with_results"],
                "provenance_reason": None,
            },
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "classification_conflict_requires_review"
    assert summary["history_signals"] == [
        "repeated_no_op_attempts",
        "validation_conflict",
        "missing_no_op_explanation",
    ]
    assert summary["operator_summary"] == (
        "Executor history has validation conflicts, no-op explanation gaps, and "
        "retry pressure; review all recommended actions before another retry."
    )
    assert [action["id"] for action in summary["recommended_actions"]] == [
        "review_validation_conflict",
        "require_no_op_explanation",
        "inspect_no_op_pattern",
    ]
    assert summary["rule_status_counts"] == {"clear": 4, "attention": 3, "blocked": 0}


def test_build_dry_run_summary_prioritizes_validation_conflict_over_rejected_retry_pressure() -> (
    None
):
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "partial",
                "ingest_status": "rejected_stale",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "result_status": "partial",
                "ingest_status": "rejected_mismatch",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": None,
                "warning_ids": ["validation_summary_conflicts_with_results"],
                "provenance_reason": None,
            },
        ]
    )

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "classification_conflict_requires_review"
    assert summary["history_signals"] == [
        "repeated_partial_attempts",
        "repeated_rejected_attempts",
        "validation_conflict",
    ]
    assert summary["operator_decision"] == "review_validation_conflict"
    assert summary["next_recommendation"] == (
        "review executor validation conflict before another retry"
    )
    assert summary["operator_summary"] == (
        "Executor history has validation conflicts and retry pressure; review both "
        "recommended actions before another retry."
    )
    assert [action["id"] for action in summary["recommended_actions"]] == [
        "review_validation_conflict",
        "inspect_rejected_results",
        "inspect_partial_attempts",
    ]
    assert summary["rule_status_counts"] == {"clear": 5, "attention": 2, "blocked": 0}


def test_build_dry_run_summary_blocks_completed_attempts_without_clean_verify() -> None:
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "completed",
                "ingest_status": "accepted_with_warning",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": "mixed",
                "warning_ids": [],
                "provenance_reason": None,
            }
        ]
    )

    assert summary["verdict"] == "blocked"
    assert summary["verdict_reason"] == "completed_attempt_not_verification_clean"
    assert summary["history_signals"] == ["completed_verify_blocked"]
    assert summary["operator_decision"] == "resolve_verification_blockers"
    assert summary["next_recommendation"] == (
        "resolve verification blocking evidence before another completed attempt"
    )
    assert summary["operator_summary"] == (
        "A completed executor attempt is still blocked by verification evidence."
    )
    assert summary["recommended_actions"] == [
        {
            "id": "resolve_verification_blockers",
            "summary": (
                "Review verify/summary.json and repair remaining or regressed "
                "blockers before accepting completion."
            ),
        }
    ]
    assert summary["rule_status_counts"] == {"clear": 6, "attention": 0, "blocked": 1}


def test_build_dry_run_summary_keeps_blocked_priority_while_explaining_attention_residue() -> (
    None
):
    summary = build_summary(
        [
            {
                "attempt_id": "attempt-1",
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": None,
                "warning_ids": [],
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-3",
                "result_status": "completed",
                "ingest_status": "accepted_with_warning",
                "verify_resume_status": "verify_blocked",
                "verification_verdict": "mixed",
                "warning_ids": ["completed_validation_failed"],
                "provenance_reason": None,
            },
        ]
    )

    assert summary["verdict"] == "blocked"
    assert summary["verdict_reason"] == "completed_attempt_not_verification_clean"
    assert summary["history_signals"] == [
        "repeated_partial_attempts",
        "completed_verify_blocked",
        "validation_conflict",
    ]
    assert summary["operator_decision"] == "resolve_verification_blockers"
    assert summary["next_recommendation"] == (
        "resolve verification blocking evidence before another completed attempt"
    )
    assert summary["operator_summary"] == (
        "A completed executor attempt is still blocked by verification evidence; "
        "validation conflicts and retry pressure still need review before another "
        "retry."
    )
    assert [action["id"] for action in summary["recommended_actions"]] == [
        "resolve_verification_blockers",
        "review_validation_conflict",
        "inspect_partial_attempts",
    ]
    assert summary["rule_status_counts"] == {"clear": 4, "attention": 2, "blocked": 1}


def test_build_dry_run_summary_guides_operators_when_history_is_empty() -> None:
    summary = build_summary([])

    assert summary["verdict"] == "attention_required"
    assert summary["verdict_reason"] == "no_recorded_attempts"
    assert summary["history_signals"] == ["no_recorded_attempts"]
    assert summary["operator_decision"] == "ingest_executor_result"
    assert summary["next_recommendation"] == (
        "ingest executor result before relying on dry-run safety evidence"
    )
    assert summary["operator_summary"] == (
        "No executor attempts are recorded for this session."
    )
    assert summary["recommended_actions"] == [
        {
            "id": "ingest_executor_result",
            "summary": (
                "Run executor-result ingest for a completed external attempt before "
                "relying on dry-run safety evidence."
            ),
        }
    ]
    assert [
        item["id"]
        for item in summary["rule_evaluations"]
        if item["status"] == "attention"
    ] == ["executor_history_recorded"]
    assert summary["rule_status_counts"] == {"clear": 6, "attention": 1, "blocked": 0}
