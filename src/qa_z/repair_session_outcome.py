"""Outcome and summary helpers for repair-session surfaces."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from qa_z.operator_action_render import render_recommended_action_lines
from qa_z.repair_session_dry_run import (
    normalized_dry_run_actions,
)

if TYPE_CHECKING:
    from qa_z.repair_session import RepairSession
    from qa_z.verification import VerificationComparison


def session_status_dict(
    session: "RepairSession", *, dry_run_summary: dict[str, Any] | None
) -> dict[str, Any]:
    """Render repair-session status as JSON-safe data with optional dry-run fields."""
    payload = session.to_dict()
    if dry_run_summary:
        payload["executor_dry_run_verdict"] = dry_run_summary.get("verdict")
        payload["executor_dry_run_reason"] = dry_run_summary.get("verdict_reason")
        payload["executor_dry_run_source"] = dry_run_summary.get("summary_source")
        payload["executor_dry_run_attempt_count"] = dry_run_summary.get(
            "evaluated_attempt_count"
        )
        payload["executor_dry_run_history_signals"] = [
            str(item)
            for item in dry_run_summary.get("history_signals", [])
            if str(item).strip()
        ]
        if dry_run_summary.get("operator_decision"):
            payload["executor_dry_run_operator_decision"] = dry_run_summary.get(
                "operator_decision"
            )
        if dry_run_summary.get("operator_summary"):
            payload["executor_dry_run_operator_summary"] = dry_run_summary.get(
                "operator_summary"
            )
        actions = normalized_dry_run_actions(dry_run_summary.get("recommended_actions"))
        if actions:
            payload["executor_dry_run_recommended_actions"] = actions
    return payload


def session_summary_json(summary: dict[str, Any]) -> str:
    """Render session summary JSON for stdout."""
    return json.dumps(summary, indent=2, sort_keys=True) + "\n"


def session_summary_dict(
    session: "RepairSession",
    comparison: "VerificationComparison",
    *,
    dry_run_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the compact top-level session summary."""
    comparison_summary = comparison.summary
    summary = {
        "kind": "qa_z.repair_session_summary",
        "schema_version": 1,
        "session_id": session.session_id,
        "state": session.state,
        "baseline_run_dir": session.baseline_run_dir,
        "candidate_run_dir": session.candidate_run_dir,
        "verify_dir": session.verify_dir,
        "outcome_path": session.outcome_path,
        "verdict": comparison.verdict,
        "repair_improved": comparison.verdict == "improved",
        "blocking_before": comparison_summary["blocking_before"],
        "blocking_after": comparison_summary["blocking_after"],
        "resolved_count": comparison_summary["resolved_count"],
        "remaining_issue_count": comparison_summary["blocking_after"],
        "new_issue_count": comparison_summary["new_issue_count"],
        "regression_count": comparison_summary["regression_count"],
        "not_comparable_count": comparison_summary["not_comparable_count"],
        "next_recommendation": recommendation_for_verdict(comparison.verdict),
    }
    if dry_run_summary:
        summary["executor_dry_run_verdict"] = dry_run_summary.get("verdict")
        summary["executor_dry_run_reason"] = dry_run_summary.get("verdict_reason")
        summary["executor_dry_run_source"] = dry_run_summary.get("summary_source")
        summary["executor_dry_run_attempt_count"] = dry_run_summary.get(
            "evaluated_attempt_count"
        )
        summary["executor_dry_run_history_signals"] = [
            str(item)
            for item in dry_run_summary.get("history_signals", [])
            if str(item).strip()
        ]
        summary["executor_dry_run_next_recommendation"] = dry_run_summary.get(
            "next_recommendation"
        )
        if dry_run_summary.get("operator_decision"):
            summary["executor_dry_run_operator_decision"] = dry_run_summary.get(
                "operator_decision"
            )
        if dry_run_summary.get("operator_summary"):
            summary["executor_dry_run_operator_summary"] = dry_run_summary.get(
                "operator_summary"
            )
        actions = normalized_dry_run_actions(dry_run_summary.get("recommended_actions"))
        if actions:
            summary["executor_dry_run_recommended_actions"] = actions
    return summary


def render_outcome_markdown(
    session: "RepairSession",
    comparison: "VerificationComparison",
    summary: dict[str, Any],
) -> str:
    """Render a human-readable session outcome."""
    lines = [
        "# QA-Z Repair Session Outcome",
        "",
        f"- Final verdict: `{comparison.verdict}`",
        f"- Next recommendation: {summary['next_recommendation']}",
        f"- Session: `{session.session_dir}`",
        f"- Baseline run: `{session.baseline_run_dir}`",
        f"- Candidate run: `{session.candidate_run_dir or 'none'}`",
        f"- Verify artifacts: `{session.verify_dir or 'none'}`",
        f"- Executor result: `{session.executor_result_status or 'none'}`",
        "",
        "## Counts",
        "",
        f"- Blocking before: {summary['blocking_before']}",
        f"- Blocking after: {summary['blocking_after']}",
        f"- Resolved issues: {summary['resolved_count']}",
        f"- Remaining issues: {summary['remaining_issue_count']}",
        f"- New or regressed issues: {summary['new_issue_count']}",
        f"- Regressions: {summary['regression_count']}",
        f"- Not comparable: {summary['not_comparable_count']}",
        "",
        "## Evidence",
        "",
        f"- Verify summary: `{session.verify_artifacts.get('summary_json', 'none')}`",
        f"- Verify compare: `{session.verify_artifacts.get('compare_json', 'none')}`",
        f"- Verify report: `{session.verify_artifacts.get('report_markdown', 'none')}`",
    ]
    if summary.get("executor_dry_run_verdict"):
        lines.extend(
            [
                "",
                "## Executor Dry-Run",
                "",
                f"- Executor dry-run verdict: `{summary['executor_dry_run_verdict']}`",
                (
                    f"- Dry-run reason: `{summary['executor_dry_run_reason']}`"
                    if summary.get("executor_dry_run_reason")
                    else "- Dry-run reason: `unknown`"
                ),
                (
                    f"- Dry-run source: `{summary['executor_dry_run_source']}`"
                    if summary.get("executor_dry_run_source")
                    else "- Dry-run source: `unknown`"
                ),
                (
                    f"- Dry-run attempts: `{summary['executor_dry_run_attempt_count']}`"
                    if summary.get("executor_dry_run_attempt_count") is not None
                    else "- Dry-run attempts: `unknown`"
                ),
                (
                    "- Dry-run history signals: "
                    + ", ".join(
                        f"`{signal}`"
                        for signal in summary.get(
                            "executor_dry_run_history_signals", []
                        )
                    )
                    if summary.get("executor_dry_run_history_signals")
                    else "- Dry-run history signals: `none`"
                ),
                (
                    "- Dry-run next recommendation: "
                    f"{summary['executor_dry_run_next_recommendation']}"
                ),
            ]
        )
        operator = str(summary.get("executor_dry_run_operator_summary") or "").strip()
        decision = str(summary.get("executor_dry_run_operator_decision") or "").strip()
        if decision:
            lines.append(f"- Dry-run operator decision: `{decision}`")
        if operator:
            lines.append(f"- Dry-run operator summary: {operator}")
        action_lines = render_recommended_action_lines(
            summary.get("executor_dry_run_recommended_actions"),
            include_action_label=True,
        )
        if action_lines != ["- none"]:
            lines.append("- Dry-run recommended actions:")
            lines.extend(action_lines)
    return "\n".join(lines).strip() + "\n"


def recommendation_for_verdict(verdict: str) -> str:
    """Return the deterministic next step for a verification verdict."""
    if verdict == "improved":
        return "merge candidate"
    if verdict == "mixed":
        return "inspect regressions"
    if verdict == "regressed":
        return "reject repair"
    if verdict == "verification_failed":
        return "rerun needed"
    return "continue repair"
