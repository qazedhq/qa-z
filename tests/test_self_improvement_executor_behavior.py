"""Tests for self-improvement executor-related behavior."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.self_improvement import BacklogCandidate, run_self_inspection, score_candidate
from tests.self_improvement_test_support import (
    write_executor_dry_run_summary,
    write_executor_ingest_record,
    write_executor_result_history,
    write_executor_result_session,
)


NOW = "2026-04-15T00:00:00Z"


def test_self_inspection_discovers_executor_result_candidates(tmp_path: Path) -> None:
    write_executor_result_session(
        tmp_path,
        session_id="session-partial",
        state="candidate_generated",
        result_status="partial",
        validation_status="failed",
        verification_hint="skip",
        now=NOW,
    )
    write_executor_result_session(
        tmp_path,
        session_id="session-no-op",
        state="failed",
        result_status="no_op",
        validation_status="not_run",
        verification_hint="skip",
        now=NOW,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="executor-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    executor_items = [
        candidate
        for candidate in report["candidates"]
        if candidate["category"] == "executor_result_gap"
    ]

    assert report["loop_id"] == "executor-loop"
    assert [item["id"] for item in executor_items] == [
        "executor_result_gap-session-no-op",
        "executor_result_gap-session-partial",
    ]
    assert {item["recommendation"] for item in executor_items} == {
        "inspect_executor_no_op",
        "resume_executor_repair",
    }
    assert any(
        "status=no_op; validation=not_run; hint=skip" in item["evidence"][0]["summary"]
        for item in executor_items
    )
    assert any(
        "status=partial; validation=failed; hint=skip" in item["evidence"][0]["summary"]
        for item in executor_items
    )


def test_self_inspection_discovers_repeated_executor_history_candidates(
    tmp_path: Path,
) -> None:
    write_executor_result_history(
        tmp_path,
        session_id="session-history",
        attempts=[
            {
                "attempt_id": "attempt-one",
                "recorded_at": NOW,
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-history/executor_results/attempts/attempt-one.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-one/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-one/ingest_report.md",
            },
            {
                "attempt_id": "attempt-two",
                "recorded_at": NOW,
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-history/executor_results/attempts/attempt-two.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-two/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-two/ingest_report.md",
            },
        ],
        now=NOW,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="history-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {candidate["category"] for candidate in report["candidates"]}

    assert "partial_completion_gap" in categories


def test_self_inspection_uses_blocked_dry_run_summary_for_single_attempt_history(
    tmp_path: Path,
) -> None:
    write_executor_result_history(
        tmp_path,
        session_id="session-blocked",
        attempts=[
            {
                "attempt_id": "attempt-one",
                "recorded_at": NOW,
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "completed",
                "ingest_status": "accepted_with_warning",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "rerun",
                "verification_triggered": False,
                "verification_verdict": "mixed",
                "validation_status": "failed",
                "warning_ids": ["completed_validation_failed"],
                "backlog_categories": ["workflow_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-blocked/executor_results/attempts/attempt-one.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-one/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-one/ingest_report.md",
            }
        ],
        now=NOW,
    )
    write_executor_dry_run_summary(
        tmp_path,
        session_id="session-blocked",
        verdict="blocked",
        verdict_reason="completed_attempt_not_verification_clean",
        history_signals=["completed_verify_blocked", "validation_conflict"],
        next_recommendation="resolve verification blocking evidence before another completed attempt",
        latest_result_status="completed",
        latest_ingest_status="accepted_with_warning",
        rule_status_counts={"attention": 1, "blocked": 1, "clear": 4},
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="dry-run-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    workflow_candidates = [
        item for item in report["candidates"] if item["category"] == "workflow_gap"
    ]

    assert workflow_candidates
    assert any(
        evidence["source"] == "executor_result_dry_run"
        and evidence["path"].endswith("dry_run_summary.json")
        for evidence in workflow_candidates[0]["evidence"]
    )
    assert "executor_dry_run_blocked" in workflow_candidates[0]["signals"]
    assert any(
        "dry_run=blocked" in evidence["summary"]
        and "source=materialized" in evidence["summary"]
        for evidence in workflow_candidates[0]["evidence"]
    )


def test_self_inspection_uses_dry_run_signal_for_missing_no_op_explanation(
    tmp_path: Path,
) -> None:
    write_executor_result_history(
        tmp_path,
        session_id="session-noop",
        attempts=[
            {
                "attempt_id": "attempt-one",
                "recorded_at": NOW,
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "not_run",
                "warning_ids": ["no_op_without_explanation"],
                "backlog_categories": ["no_op_safeguard_gap"],
                "changed_files_count": 0,
                "notes_count": 0,
                "attempt_path": ".qa-z/sessions/session-noop/executor_results/attempts/attempt-one.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-one/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-one/ingest_report.md",
            }
        ],
        now=NOW,
    )
    write_executor_dry_run_summary(
        tmp_path,
        session_id="session-noop",
        verdict="attention_required",
        verdict_reason="manual_retry_review_required",
        history_signals=["missing_no_op_explanation"],
        next_recommendation="inspect executor attempt history before another retry",
        latest_result_status="no_op",
        latest_ingest_status="accepted_no_op",
        rule_status_counts={"attention": 1, "blocked": 0, "clear": 5},
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="noop-dry-run-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    noop_candidates = [
        item
        for item in report["candidates"]
        if item["category"] == "no_op_safeguard_gap"
    ]

    assert noop_candidates
    assert "executor_dry_run_attention" in noop_candidates[0]["signals"]
    assert any(
        evidence["source"] == "executor_result_dry_run"
        and "source=materialized" in evidence["summary"]
        for evidence in noop_candidates[0]["evidence"]
    )


def test_self_inspection_synthesizes_dry_run_from_history_when_summary_is_missing(
    tmp_path: Path,
) -> None:
    write_executor_result_history(
        tmp_path,
        session_id="session-partial",
        attempts=[
            {
                "attempt_id": "attempt-one",
                "recorded_at": "2026-04-16T00:00:01Z",
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-partial/executor_results/attempts/attempt-one.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-one/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-one/ingest_report.md",
            },
            {
                "attempt_id": "attempt-two",
                "recorded_at": "2026-04-16T00:00:02Z",
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-partial/executor_results/attempts/attempt-two.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-two/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-two/ingest_report.md",
            },
        ],
        now=NOW,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="partial-fallback-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    partial_candidates = [
        item
        for item in report["candidates"]
        if item["category"] == "partial_completion_gap"
    ]

    assert partial_candidates
    assert "executor_dry_run_attention" in partial_candidates[0]["signals"]
    assert any(
        evidence["source"] == "executor_result_dry_run_fallback"
        and "dry_run=attention_required" in evidence["summary"]
        and "source=history_fallback" in evidence["summary"]
        for evidence in partial_candidates[0]["evidence"]
    )


def test_self_inspection_promotes_executor_ingest_backlog_implications(
    tmp_path: Path,
) -> None:
    write_executor_ingest_record(
        tmp_path,
        record_id="stale-one",
        ingest_status="rejected_stale",
        result_status="completed",
        verify_resume_status="stale_result",
        backlog_implications=[
            {
                "id": "evidence_freshness_gap-stale-one",
                "title": "Harden executor result freshness handling",
                "category": "evidence_freshness_gap",
                "recommendation": "harden_executor_result_freshness",
                "signals": ["executor_result_stale"],
                "impact": 3,
                "likelihood": 4,
                "confidence": 4,
                "repair_cost": 3,
                "summary": "stale result blocked verification resume",
            }
        ],
    )
    write_executor_ingest_record(
        tmp_path,
        record_id="mismatch-one",
        ingest_status="rejected_mismatch",
        result_status="completed",
        verify_resume_status="mismatch_detected",
        backlog_implications=[
            {
                "id": "provenance_gap-mismatch-one",
                "title": "Harden executor provenance validation",
                "category": "provenance_gap",
                "recommendation": "audit_executor_contract",
                "signals": ["executor_result_provenance_mismatch"],
                "impact": 4,
                "likelihood": 4,
                "confidence": 4,
                "repair_cost": 3,
                "summary": "bridge/session provenance mismatch rejected ingest",
            }
        ],
    )
    write_executor_ingest_record(
        tmp_path,
        record_id="partial-one",
        ingest_status="accepted_partial",
        result_status="partial",
        verify_resume_status="verify_blocked",
        backlog_implications=[
            {
                "id": "partial_completion_gap-partial-one",
                "title": "Harden partial completion ingest handling",
                "category": "partial_completion_gap",
                "recommendation": "harden_partial_completion_handling",
                "signals": ["executor_result_partial"],
                "impact": 3,
                "likelihood": 4,
                "confidence": 4,
                "repair_cost": 3,
                "summary": "partial result blocked immediate verify",
            }
        ],
    )
    write_executor_ingest_record(
        tmp_path,
        record_id="noop-one",
        ingest_status="accepted_no_op",
        result_status="no_op",
        verify_resume_status="verify_blocked",
        backlog_implications=[
            {
                "id": "no_op_safeguard_gap-noop-one",
                "title": "Harden no-op executor result safeguards",
                "category": "no_op_safeguard_gap",
                "recommendation": "harden_executor_no_op_safeguards",
                "signals": ["executor_result_no_op"],
                "impact": 3,
                "likelihood": 3,
                "confidence": 4,
                "repair_cost": 2,
                "summary": "no-op result lacked a strong explanation",
            }
        ],
    )
    write_executor_ingest_record(
        tmp_path,
        record_id="validation-one",
        ingest_status="accepted_with_warning",
        result_status="completed",
        verify_resume_status="verify_blocked",
        backlog_implications=[
            {
                "id": "workflow_gap-validation-one",
                "title": "Harden executor validation evidence consistency",
                "category": "workflow_gap",
                "recommendation": "audit_executor_contract",
                "signals": ["executor_validation_failed"],
                "impact": 3,
                "likelihood": 3,
                "confidence": 4,
                "repair_cost": 2,
                "summary": "validation metadata conflicted with detailed executor results",
            }
        ],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="ingest-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    categories = {item["category"] for item in report["candidates"]}

    assert "evidence_freshness_gap" in categories
    assert "provenance_gap" in categories
    assert "partial_completion_gap" in categories
    assert "no_op_safeguard_gap" in categories
    assert "workflow_gap" in categories
    assert any(
        item["recommendation"] == "audit_executor_contract"
        for item in report["candidates"]
        if item["category"] in {"provenance_gap", "workflow_gap"}
    )


def test_score_candidate_boosts_executor_result_safety_signals() -> None:
    candidate = BacklogCandidate(
        id="executor_result_gap-session-no-op",
        title="Inspect executor no-op result: session-no-op",
        category="executor_result_gap",
        evidence=[
            {
                "source": "executor_result",
                "path": ".qa-z/sessions/session-no-op/executor_result.json",
                "summary": "status=no_op; validation=failed; hint=skip",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=3,
        repair_cost=5,
        recommendation="inspect_executor_no_op",
        signals=["executor_validation_failed", "executor_result_no_op"],
    )

    score = score_candidate(candidate)

    assert score == 46


def test_score_candidate_prioritizes_blocked_dry_run_over_attention() -> None:
    blocked_candidate = BacklogCandidate(
        id="workflow_gap-session-blocked",
        title="Audit repeated executor attempt friction: session-blocked",
        category="workflow_gap",
        evidence=[{"source": "executor_result_dry_run", "path": "blocked.json"}],
        impact=3,
        likelihood=4,
        confidence=4,
        repair_cost=3,
        recommendation="audit_executor_contract",
        signals=[
            "service_readiness_gap",
            "regression_prevention",
            "executor_dry_run_blocked",
        ],
    )
    attention_candidate = BacklogCandidate(
        id="no_op_safeguard_gap-session-noop",
        title="Inspect repeated no-op executor attempts: session-noop",
        category="no_op_safeguard_gap",
        evidence=[{"source": "executor_result_dry_run", "path": "attention.json"}],
        impact=3,
        likelihood=4,
        confidence=4,
        repair_cost=3,
        recommendation="harden_executor_no_op_safeguards",
        signals=[
            "executor_result_no_op",
            "regression_prevention",
            "executor_dry_run_attention",
        ],
    )

    assert score_candidate(blocked_candidate) > score_candidate(attention_candidate)
