"""Tests for executor-related self-improvement signal inputs."""

from __future__ import annotations

from pathlib import Path

import qa_z.executor_history_signals as executor_history_signals_module
import qa_z.executor_signals as executor_signals_module
from tests.self_improvement_test_support import write_json


NOW = "2026-04-15T00:00:00Z"


def test_discover_executor_result_candidate_inputs_uses_manifest_fallback(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "sessions" / "session-one" / "session.json",
        {
            "kind": "qa_z.repair_session",
            "schema_version": 1,
            "session_id": "session-one",
            "executor_result_status": " failed ",
            "executor_result_validation_status": " failed ",
            "executor_result_path": ".qa-z/sessions/session-one/missing-result.json",
        },
    )

    candidates = executor_signals_module.discover_executor_result_candidate_inputs(
        tmp_path
    )

    assert candidates == [
        {
            "session_id": "session-one",
            "path": tmp_path / ".qa-z" / "sessions" / "session-one" / "session.json",
            "result_status": "failed",
            "validation_status": "failed",
            "verification_hint": "skip",
            "recommendation": "triage_executor_failure",
            "title": "Triage failed executor result: session-one",
            "signals": ["executor_result_failed", "executor_validation_failed"],
            "impact": 4,
            "confidence": 4,
        }
    ]


def test_discover_executor_ingest_candidate_inputs_skips_partial_implications(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "executor-results" / "record-one" / "ingest.json",
        {
            "kind": "qa_z.executor_result_ingest",
            "schema_version": 1,
            "ingest_status": "accepted",
            "backlog_implications": [
                {
                    "id": " executor_gap-one ",
                    "category": " workflow_gap ",
                    "recommendation": " audit_worktree_integration ",
                    "title": " Audit worktree integration ",
                    "summary": "executor implication",
                    "signals": [" executor_result_partial "],
                    "impact": 0,
                    "likelihood": 2,
                    "confidence": 3,
                    "repair_cost": 0,
                },
                {
                    "id": "executor_gap-two",
                    "category": "workflow_gap",
                    "recommendation": "audit_worktree_integration",
                    "summary": "missing title should skip",
                },
            ],
        },
    )

    candidates = executor_signals_module.discover_executor_ingest_candidate_inputs(
        tmp_path
    )

    assert candidates == [
        {
            "id": "executor_gap-one",
            "title": "Audit worktree integration",
            "category": "workflow_gap",
            "path": tmp_path
            / ".qa-z"
            / "executor-results"
            / "record-one"
            / "ingest.json",
            "summary": "executor implication",
            "impact": 1,
            "likelihood": 2,
            "confidence": 3,
            "repair_cost": 1,
            "recommendation": "audit_worktree_integration",
            "signals": ["executor_result_partial"],
        }
    ]


def test_load_or_synthesize_executor_dry_run_summary_marks_history_fallback(
    tmp_path: Path,
) -> None:
    history_path = (
        tmp_path
        / ".qa-z"
        / "sessions"
        / "session-one"
        / "executor_results"
        / "history.json"
    )
    attempts = [
        {
            "attempt_id": "attempt-one",
            "result_status": "partial",
            "ingest_status": "accepted",
        },
        {
            "attempt_id": "attempt-two",
            "result_status": "partial",
            "ingest_status": "accepted",
        },
    ]

    summary, used_fallback = (
        executor_history_signals_module.load_or_synthesize_executor_dry_run_summary(
            root=tmp_path,
            history_path=history_path,
            summary_path=history_path.parent / "dry_run_summary.json",
            session_id="session-one",
            attempts=attempts,
        )
    )

    assert used_fallback is True
    assert summary["summary_source"] == "history_fallback"
    assert (
        summary["history_path"]
        == ".qa-z/sessions/session-one/executor_results/history.json"
    )


def test_discover_executor_history_candidate_inputs_records_fallback_evidence_source(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path
        / ".qa-z"
        / "sessions"
        / "session-history"
        / "executor_results"
        / "history.json",
        {
            "kind": "qa_z.executor_result_history",
            "schema_version": 1,
            "session_id": "session-history",
            "updated_at": NOW,
            "attempt_count": 2,
            "latest_attempt_id": "attempt-two",
            "attempts": [
                {
                    "attempt_id": "attempt-one",
                    "created_at": NOW,
                    "result_status": "partial",
                    "ingest_status": "accepted",
                    "attempt_path": ".qa-z/sessions/session-history/executor_results/attempts/attempt-one.json",
                },
                {
                    "attempt_id": "attempt-two",
                    "created_at": NOW,
                    "result_status": "partial",
                    "ingest_status": "accepted",
                    "attempt_path": ".qa-z/sessions/session-history/executor_results/attempts/attempt-two.json",
                },
            ],
        },
    )

    candidates = (
        executor_history_signals_module.discover_executor_history_candidate_inputs(
            tmp_path
        )
    )

    partial_candidate = next(
        item for item in candidates if item["category"] == "partial_completion_gap"
    )
    dry_run_evidence = next(
        evidence
        for evidence in partial_candidate["evidence"]
        if evidence["source"] == "executor_result_dry_run_fallback"
    )

    assert partial_candidate["signals"] == [
        "executor_result_partial",
        "regression_prevention",
        "executor_dry_run_attention",
    ]
    assert dry_run_evidence["path"] == (
        tmp_path
        / ".qa-z"
        / "sessions"
        / "session-history"
        / "executor_results"
        / "history.json"
    )
    assert "source=history_fallback" in dry_run_evidence["summary"]
