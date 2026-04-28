"""Behavior tests for executor dry-run rendering helpers."""

from __future__ import annotations

from qa_z.executor_dry_run_render import (
    normalize_recommended_actions,
    render_dry_run_report,
)


def test_normalize_recommended_actions_filters_invalid_items() -> None:
    actions = normalize_recommended_actions(
        [
            {"id": "inspect_scope", "summary": "Review scope drift."},
            {"id": "", "summary": "missing id"},
            {"id": "missing-summary", "summary": ""},
            "not-a-dict",
        ]
    )

    assert actions == [{"id": "inspect_scope", "summary": "Review scope drift."}]


def test_render_dry_run_report_renders_rule_counts_and_actions() -> None:
    report = render_dry_run_report(
        {
            "session_id": "session-one",
            "summary_source": "materialized",
            "verdict": "attention_required",
            "verdict_reason": "manual_retry_review_required",
            "evaluated_attempt_count": 2,
            "latest_attempt_id": "attempt-2",
            "safety_package_id": "pre_live_executor_safety_v1",
            "operator_decision": "inspect_partial_attempts",
            "operator_summary": "Repeated partial attempts need review.",
            "next_recommendation": "inspect repeated partial attempts before another retry",
            "rule_status_counts": {"clear": 6, "attention": 1, "blocked": 0},
            "history_signals": ["repeated_partial_attempts"],
            "recommended_actions": [
                {
                    "id": "inspect_partial_attempts",
                    "summary": "Review unresolved repair targets before retrying.",
                }
            ],
            "rule_evaluations": [
                {
                    "id": "retry_boundary_is_manual",
                    "status": "attention",
                    "summary": "Repeated attempts need explicit manual review.",
                }
            ],
        }
    )

    assert "- Rule counts: clear=6, attention=1, blocked=0" in report
    assert (
        "- `inspect_partial_attempts`: Review unresolved repair targets before retrying."
        in report
    )
    assert (
        "- `retry_boundary_is_manual` -> `attention`: Repeated attempts need explicit manual review."
        in report
    )
