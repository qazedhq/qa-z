"""Executor-oriented benchmark actual-summary helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.benchmark_helpers import coerce_mapping, unique_strings
from qa_z.executor_bridge import render_bridge_stdout
from qa_z.executor_ingest import render_executor_result_ingest_stdout


def summarize_executor_bridge_actual(
    *, workspace: Path, manifest: dict[str, Any], guide: str
) -> dict[str, Any]:
    """Return benchmark-relevant executor bridge packaging observations."""
    inputs = coerce_mapping(manifest.get("inputs"))
    context_items = inputs.get("action_context", [])
    if not isinstance(context_items, list):
        context_items = []
    action_context = [dict(item) for item in context_items if isinstance(item, dict)]
    copied_paths = [
        str(item.get("copied_path"))
        for item in action_context
        if str(item.get("copied_path") or "").strip()
    ]
    missing_items = inputs.get("action_context_missing", [])
    if not isinstance(missing_items, list):
        missing_items = []
    missing_context = [str(item) for item in missing_items if str(item).strip()]
    stdout = render_bridge_stdout(manifest)
    live_repository = coerce_mapping(manifest.get("live_repository"))
    return {
        "kind": manifest.get("kind"),
        "schema_version": manifest.get("schema_version"),
        "bridge_id": manifest.get("bridge_id"),
        "source_loop_id": manifest.get("source_loop_id"),
        "source_session_id": manifest.get("source_session_id"),
        "source_self_inspection": manifest.get("source_self_inspection"),
        "source_self_inspection_loop_id": manifest.get(
            "source_self_inspection_loop_id"
        ),
        "source_self_inspection_generated_at": manifest.get(
            "source_self_inspection_generated_at"
        ),
        "live_repository_modified_count": live_repository.get("modified_count"),
        "live_repository_current_branch": live_repository.get("current_branch"),
        "live_repository_current_head": live_repository.get("current_head"),
        "prepared_action_type": manifest.get("prepared_action_type"),
        "action_context_count": len(action_context),
        "action_context_paths": [
            str(item.get("source_path"))
            for item in action_context
            if str(item.get("source_path") or "").strip()
        ],
        "action_context_copied_paths": copied_paths,
        "action_context_missing": missing_context,
        "action_context_missing_count": len(missing_context),
        "action_context_files_exist": all(
            (workspace / copied_path).is_file() for copied_path in copied_paths
        ),
        "guide_mentions_action_context": (
            "Action context" in guide
            and all(copied_path in guide for copied_path in copied_paths)
        ),
        "guide_mentions_live_repository": "Live Repository Context" in guide,
        "guide_mentions_missing_action_context": (
            "Action context missing" in guide
            and all(missing_path in guide for missing_path in missing_context)
        ),
        "stdout_mentions_action_context": (
            f"Action context inputs: {len(action_context)}" in stdout
        ),
        "stdout_mentions_missing_action_context": (
            "Missing action context:" in stdout
            and all(missing_path in stdout for missing_path in missing_context)
        ),
    }


def summarize_executor_result_actual(summary: dict[str, Any]) -> dict[str, Any]:
    """Return benchmark-relevant executor-result ingest observations."""
    backlog_implications = [
        dict(item)
        for item in summary.get("backlog_implications", [])
        if isinstance(item, dict)
    ]
    freshness_check = coerce_mapping(summary.get("freshness_check"))
    provenance_check = coerce_mapping(summary.get("provenance_check"))
    live_repository = coerce_mapping(summary.get("live_repository"))
    stdout = render_executor_result_ingest_stdout(summary)
    backlog_categories = unique_strings(
        [
            str(item.get("category") or "")
            for item in backlog_implications
            if str(item.get("category") or "").strip()
        ]
    )
    source_context_fields_recorded = all(
        str(summary.get(key) or "").strip()
        for key in (
            "source_self_inspection",
            "source_self_inspection_loop_id",
            "source_self_inspection_generated_at",
        )
    )
    return {
        "kind": summary.get("kind"),
        "schema_version": summary.get("schema_version"),
        "bridge_id": summary.get("bridge_id"),
        "session_id": summary.get("session_id"),
        "source_self_inspection": summary.get("source_self_inspection"),
        "source_self_inspection_loop_id": summary.get("source_self_inspection_loop_id"),
        "source_self_inspection_generated_at": summary.get(
            "source_self_inspection_generated_at"
        ),
        "live_repository_modified_count": live_repository.get("modified_count"),
        "live_repository_current_branch": live_repository.get("current_branch"),
        "live_repository_current_head": live_repository.get("current_head"),
        "result_status": summary.get("result_status"),
        "ingest_status": summary.get("ingest_status"),
        "session_state": summary.get("session_state"),
        "verification_hint": summary.get("verification_hint"),
        "verification_triggered": summary.get("verification_triggered"),
        "verification_verdict": summary.get("verification_verdict"),
        "verify_resume_status": summary.get("verify_resume_status"),
        "verify_summary_path": summary.get("verify_summary_path"),
        "freshness_status": freshness_check.get("status"),
        "freshness_reason": freshness_check.get("reason"),
        "provenance_status": provenance_check.get("status"),
        "provenance_reason": provenance_check.get("reason"),
        "warning_ids": list(summary.get("warnings") or []),
        "backlog_categories": backlog_categories,
        "source_context_fields_recorded": source_context_fields_recorded,
        "live_repository_context_recorded": bool(live_repository),
        "check_statuses_recorded": bool(
            freshness_check.get("status") and provenance_check.get("status")
        ),
        "backlog_implications_recorded": bool(backlog_categories),
        "stdout_mentions_source_context": (
            "Source self-inspection:" in stdout
            and "Source loop:" in stdout
            and "Live repository:" in stdout
        ),
        "stdout_mentions_checks": ("Freshness:" in stdout and "Provenance:" in stdout),
        "stdout_mentions_backlog_implications": (
            "Backlog implications:" in stdout
            and all(category in stdout for category in backlog_categories)
        ),
        "next_recommendation": summary.get("next_recommendation"),
    }


def summarize_executor_dry_run_actual(summary: dict[str, Any]) -> dict[str, Any]:
    """Return benchmark-relevant executor dry-run observations."""
    evaluations = [
        dict(item)
        for item in summary.get("rule_evaluations", [])
        if isinstance(item, dict)
    ]
    actions = [
        dict(item)
        for item in summary.get("recommended_actions", [])
        if isinstance(item, dict)
    ]

    def rule_ids(status: str) -> list[str]:
        return [
            str(item.get("id"))
            for item in evaluations
            if str(item.get("id") or "").strip()
            and str(item.get("status") or "").strip() == status
        ]

    counts = summary.get("rule_status_counts")
    rule_counts = counts if isinstance(counts, dict) else {}
    return {
        "kind": summary.get("kind"),
        "schema_version": summary.get("schema_version"),
        "session_id": summary.get("session_id"),
        "summary_source": summary.get("summary_source"),
        "evaluated_attempt_count": summary.get("evaluated_attempt_count"),
        "latest_attempt_id": summary.get("latest_attempt_id"),
        "latest_result_status": summary.get("latest_result_status"),
        "latest_ingest_status": summary.get("latest_ingest_status"),
        "verdict": summary.get("verdict"),
        "verdict_reason": summary.get("verdict_reason"),
        "operator_decision": summary.get("operator_decision"),
        "operator_summary": summary.get("operator_summary"),
        "recommended_action_ids": [
            str(item.get("id")) for item in actions if str(item.get("id") or "").strip()
        ],
        "recommended_action_summaries": [
            str(item.get("summary"))
            for item in actions
            if str(item.get("summary") or "").strip()
        ],
        "history_signals": [
            str(item)
            for item in summary.get("history_signals", [])
            if str(item).strip()
        ],
        "next_recommendation": summary.get("next_recommendation"),
        "clear_rule_count": int(rule_counts.get("clear", 0) or 0),
        "attention_rule_count": int(rule_counts.get("attention", 0) or 0),
        "blocked_rule_count": int(rule_counts.get("blocked", 0) or 0),
        "attention_rule_ids": rule_ids("attention"),
        "blocked_rule_ids": rule_ids("blocked"),
        "clear_rule_ids": rule_ids("clear"),
    }


def summarize_artifact_actual(workspace: Path) -> dict[str, Any]:
    """Return generated artifact files relative to the fixture workspace."""
    runs_dir = workspace / ".qa-z" / "runs"
    if not runs_dir.exists():
        return {"files": []}
    return {
        "files": sorted(
            path.relative_to(workspace).as_posix()
            for path in runs_dir.rglob("*")
            if path.is_file()
        )
    }
