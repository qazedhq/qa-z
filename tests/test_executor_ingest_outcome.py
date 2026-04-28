"""Behavior tests for executor-ingest outcome helpers."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from qa_z.executor_ingest_outcome import (
    compact_timestamp,
    executor_result_id,
    finalized_ingest_outcome,
    ingest_source_context,
)


def test_ingest_source_context_copies_live_repository_and_loop_metadata() -> None:
    context = ingest_source_context(
        {
            "source_self_inspection": ".qa-z/loops/loop-001/self_inspect.json",
            "source_self_inspection_loop_id": "loop-001",
            "source_self_inspection_generated_at": "2026-04-22T00:00:00Z",
            "live_repository": {"dirty": True, "tracked_changes": 3},
        }
    )

    assert context == {
        "source_self_inspection": ".qa-z/loops/loop-001/self_inspect.json",
        "source_self_inspection_loop_id": "loop-001",
        "source_self_inspection_generated_at": "2026-04-22T00:00:00Z",
        "live_repository": {"dirty": True, "tracked_changes": 3},
    }


def test_executor_result_id_compacts_timestamp_for_stable_paths() -> None:
    result = SimpleNamespace(
        bridge_id="bridge-one",
        created_at="2026-04-22T03:04:05Z",
    )

    assert compact_timestamp("2026-04-22T03:04:05Z") == "20260422t030405z"
    assert executor_result_id(result) == "bridge-one-20260422t030405z"


def test_finalized_ingest_outcome_writes_machine_and_human_artifacts(
    tmp_path: Path,
) -> None:
    result = SimpleNamespace(
        bridge_id="bridge-one",
        status="completed",
        verification_hint="rerun",
    )

    outcome = finalized_ingest_outcome(
        root=tmp_path,
        result=result,
        result_id="bridge-one-20260422t030405z",
        session_id="session-one",
        source_loop_id="loop-001",
        ingest_status="accepted",
        warnings=["warning-a"],
        freshness_check={"status": "passed", "details": ["fresh enough"]},
        provenance_check={"status": "passed", "details": ["bridge matched"]},
        verify_resume_status="ready_for_verify",
        backlog_implications=[],
        next_recommendation="run verification",
        stored_result_path=tmp_path
        / ".qa-z"
        / "sessions"
        / "session-one"
        / "executor_result.json",
        session_state="completed",
        verification_triggered=True,
        verification_verdict="improved",
        verify_summary_path=tmp_path
        / ".qa-z"
        / "sessions"
        / "session-one"
        / "verify"
        / "summary.json",
        source_context={
            "source_self_inspection": ".qa-z/loops/loop-001/self_inspect.json",
            "source_self_inspection_loop_id": "loop-001",
            "source_self_inspection_generated_at": "2026-04-22T00:00:00Z",
            "live_repository": {
                "dirty": True,
                "tracked_changes": 2,
                "untracked_count": 1,
                "high_signal_paths": ["src/qa_z/executor_ingest.py"],
            },
        },
    )

    ingest_dir = tmp_path / ".qa-z" / "executor-results" / "bridge-one-20260422t030405z"
    payload = json.loads((ingest_dir / "ingest.json").read_text(encoding="utf-8"))
    report = (ingest_dir / "ingest_report.md").read_text(encoding="utf-8")

    assert outcome.summary["ingest_status"] == "accepted"
    assert payload["verify_resume_status"] == "ready_for_verify"
    assert payload["source_self_inspection_loop_id"] == "loop-001"
    assert "QA-Z Executor Result Ingest Report" in report
    assert "## Source Context" in report
    assert "## Live Repository Context" in report
