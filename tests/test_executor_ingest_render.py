"""Behavior tests for executor-ingest render helpers."""

from __future__ import annotations

from qa_z.executor_ingest_render import (
    render_executor_result_ingest_stdout,
    render_ingest_report,
)


def _summary() -> dict[str, object]:
    return {
        "result_id": "bridge-one-20260422t030405z",
        "bridge_id": "bridge-one",
        "session_id": "session-one",
        "result_status": "partial",
        "ingest_status": "accepted_partial",
        "stored_result_path": None,
        "ingest_report_path": ".qa-z/executor-results/bridge-one-20260422t030405z/ingest_report.md",
        "verify_resume_status": "verify_blocked",
        "verification_verdict": None,
        "next_recommendation": "inspect executor result warnings",
        "source_self_inspection": ".qa-z/loops/loop-001/self_inspect.json",
        "source_self_inspection_loop_id": "loop-001",
        "source_self_inspection_generated_at": "2026-04-22T00:00:00Z",
        "live_repository": {
            "dirty": True,
            "tracked_changes": 2,
            "untracked_count": 1,
            "high_signal_paths": ["src/qa_z/executor_ingest.py"],
        },
        "freshness_check": {
            "status": "warning",
            "details": ["bridge missing timestamp"],
        },
        "provenance_check": {"status": "passed", "details": []},
        "warnings": ["validation_summary_conflicts_with_results"],
        "backlog_implications": [
            {
                "category": "validation_gap",
                "summary": "Validation metadata drift remains.",
            }
        ],
    }


def test_render_executor_result_ingest_stdout_surfaces_source_context() -> None:
    output = render_executor_result_ingest_stdout(_summary())

    assert "qa-z executor-result ingest: accepted_partial" in output
    assert "Source self-inspection: .qa-z/loops/loop-001/self_inspect.json" in output
    assert "Live repository:" in output
    assert "Warnings: validation_summary_conflicts_with_results" in output


def test_render_ingest_report_surfaces_context_and_backlog_implications() -> None:
    output = render_ingest_report(_summary())

    assert "# QA-Z Executor Result Ingest Report" in output
    assert "## Source Context" in output
    assert "## Live Repository Context" in output
    assert "## Backlog Implications" in output
    assert "`validation_gap`: Validation metadata drift remains." in output
