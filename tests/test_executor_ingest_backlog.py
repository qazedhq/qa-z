"""Behavior tests for executor-ingest backlog helpers."""

from __future__ import annotations

from types import SimpleNamespace

from qa_z.executor_ingest_backlog import backlog_implications_for_ingest


def _result(*, status: str) -> SimpleNamespace:
    return SimpleNamespace(status=status)


def test_backlog_implications_flag_freshness_and_validation_gaps() -> None:
    implications = backlog_implications_for_ingest(
        result=_result(status="completed"),
        result_id="result-1",
        ingest_status="rejected_stale",
        freshness_reason="session_newer_than_result",
        provenance_reason=None,
        warnings=[
            "validation_summary_conflicts_with_results",
            "validation_result_command_not_declared",
        ],
    )

    assert {item["category"] for item in implications} == {
        "evidence_freshness_gap",
        "workflow_gap",
    }


def test_backlog_implications_flag_partial_and_no_op_gaps_once_each() -> None:
    implications = backlog_implications_for_ingest(
        result=_result(status="no_op"),
        result_id="result-2",
        ingest_status="accepted_partial",
        freshness_reason=None,
        provenance_reason="scope_mismatch",
        warnings=["completed_without_changed_files", "no_op_without_explanation"],
    )

    assert {item["category"] for item in implications} == {
        "partial_completion_gap",
        "no_op_safeguard_gap",
        "provenance_gap",
    }
