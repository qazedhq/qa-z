"""Behavior tests for executor-ingest session persistence helpers."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from qa_z.executor_ingest_session import (
    persist_ingested_result,
    record_loop_executor_result,
    resume_verification_if_ready,
)
from qa_z.executor_ingest_checks import verify_resume_status_for_result
from qa_z.executor_result import (
    ExecutorChangedFile,
    ExecutorResult,
    ExecutorValidation,
)
from qa_z.repair_session import RepairSession


def repair_session() -> RepairSession:
    """Build a compact repair session fixture."""
    return RepairSession(
        session_id="session-one",
        session_dir=".qa-z/sessions/session-one",
        baseline_run_dir=".qa-z/runs/baseline",
        handoff_dir=".qa-z/sessions/session-one/handoff",
        executor_guide_path=".qa-z/sessions/session-one/executor-guide.md",
        state="waiting_for_external_repair",
        created_at="2026-04-22T00:00:00Z",
        updated_at="2026-04-22T00:00:00Z",
        baseline_fast_summary_path=".qa-z/runs/baseline/fast/summary.json",
    )


def executor_result(
    *,
    status: str = "completed",
    verification_hint: str = "rerun",
    candidate_run_dir: str | None = None,
) -> ExecutorResult:
    """Build a deterministic executor-result fixture."""
    return ExecutorResult(
        bridge_id="bridge-one",
        source_session_id="session-one",
        source_loop_id="loop-001",
        created_at="2026-04-22T00:00:01Z",
        status=status,
        summary="Completed deterministic repair work.",
        verification_hint=verification_hint,
        candidate_run_dir=(
            candidate_run_dir
            if candidate_run_dir is not None
            else ".qa-z/runs/candidate"
            if verification_hint == "candidate_run"
            else None
        ),
        changed_files=[
            ExecutorChangedFile(
                path="src/qa_z/executor_ingest.py",
                status="modified",
                old_path=None,
                summary="Updated ingest flow.",
            )
        ],
        validation=ExecutorValidation(status="passed"),
    )


def test_persist_ingested_result_updates_session_manifest(tmp_path: Path) -> None:
    session = repair_session()
    result = executor_result(status="completed")

    updated_session, stored_result_path = persist_ingested_result(
        root=tmp_path,
        session=session,
        result=result,
    )

    manifest = json.loads(
        (tmp_path / ".qa-z" / "sessions" / "session-one" / "session.json").read_text(
            encoding="utf-8"
        )
    )

    assert stored_result_path == (
        tmp_path / ".qa-z" / "sessions" / "session-one" / "executor_result.json"
    )
    assert stored_result_path.exists()
    assert updated_session.state == "candidate_generated"
    assert updated_session.executor_result_status == "completed"
    assert manifest["state"] == "candidate_generated"
    assert manifest["executor_result_validation_status"] == "passed"
    assert manifest["executor_result_bridge_id"] == "bridge-one"


def test_resume_verification_if_ready_runs_verify_flow_when_allowed(
    tmp_path: Path,
) -> None:
    session = repair_session()
    result = executor_result(status="completed", verification_hint="candidate_run")
    calls: dict[str, object] = {}

    def fake_verify_runner(**kwargs):
        calls.update(kwargs)
        return (
            session,
            {
                "verify_dir": ".qa-z/sessions/session-one/verify",
                "next_recommendation": "publish verification",
            },
            SimpleNamespace(verdict="improved"),
        )

    updated_session, triggered, verdict, verify_summary_path, recommendation = (
        resume_verification_if_ready(
            root=tmp_path,
            config={"project": {"name": "qa-z"}},
            session=session,
            result=result,
            verify_resume_status="ready_for_verify",
            next_recommendation="run repair-session verify",
            verify_ready_statuses={"ready_for_verify", "ingested_with_warning"},
            verify_runner=fake_verify_runner,
        )
    )

    assert updated_session is session
    assert triggered is True
    assert verdict == "improved"
    assert verify_summary_path == (
        tmp_path / ".qa-z" / "sessions" / "session-one" / "verify" / "summary.json"
    )
    assert recommendation == "publish verification"
    assert calls["candidate_run"] == ".qa-z/runs/candidate"
    assert calls["rerun"] is False


def test_verify_resume_blocks_candidate_run_outside_repository(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside_candidate = tmp_path / "outside-candidate"
    (root / ".qa-z" / "runs" / "baseline").mkdir(parents=True)
    outside_candidate.mkdir()
    warnings: list[str] = []

    status = verify_resume_status_for_result(
        root=root,
        result=executor_result(
            status="completed",
            verification_hint="candidate_run",
            candidate_run_dir=str(outside_candidate),
        ),
        session=repair_session(),
        warnings=warnings,
    )

    assert status == "verify_blocked"
    assert warnings == ["candidate_run_outside_repository"]


def test_verify_resume_blocks_candidate_run_without_fast_summary(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / ".qa-z" / "runs" / "baseline").mkdir(parents=True)
    (root / ".qa-z" / "runs" / "candidate").mkdir(parents=True)
    warnings: list[str] = []

    status = verify_resume_status_for_result(
        root=root,
        result=executor_result(status="completed", verification_hint="candidate_run"),
        session=repair_session(),
        warnings=warnings,
    )

    assert status == "verify_blocked"
    assert warnings == ["candidate_run_fast_summary_missing"]


def test_verify_resume_blocks_baseline_run_outside_repository(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside_baseline = tmp_path / "outside-baseline"
    (outside_baseline / "fast").mkdir(parents=True)
    (outside_baseline / "fast" / "summary.json").write_text("{}", encoding="utf-8")
    warnings: list[str] = []

    status = verify_resume_status_for_result(
        root=root,
        result=executor_result(status="completed", verification_hint="rerun"),
        session=replace(repair_session(), baseline_run_dir=str(outside_baseline)),
        warnings=warnings,
    )

    assert status == "verify_blocked"
    assert warnings == ["baseline_run_outside_repository"]


def test_verify_resume_blocks_baseline_run_without_fast_summary(
    tmp_path: Path,
) -> None:
    root = tmp_path / "repo"
    (root / ".qa-z" / "runs" / "baseline").mkdir(parents=True)
    warnings: list[str] = []

    status = verify_resume_status_for_result(
        root=root,
        result=executor_result(status="completed", verification_hint="rerun"),
        session=repair_session(),
        warnings=warnings,
    )

    assert status == "verify_blocked"
    assert warnings == ["baseline_run_fast_summary_missing"]


def test_record_loop_executor_result_updates_matching_history_entry(
    tmp_path: Path,
) -> None:
    history_path = tmp_path / ".qa-z" / "loops" / "history.jsonl"
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps(
            {
                "kind": "qa_z.loop_history_entry",
                "loop_id": "loop-001",
                "next_recommendations": [],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    record_loop_executor_result(
        root=tmp_path,
        source_loop_id="loop-001",
        result=executor_result(status="partial", verification_hint="skip"),
        ingest_status="accepted_partial",
        verify_resume_status="verify_blocked",
        stored_result_path=tmp_path
        / ".qa-z"
        / "sessions"
        / "session-one"
        / "executor_result.json",
        verification_verdict=None,
        next_recommendation="continue repair",
    )

    payload = json.loads(history_path.read_text(encoding="utf-8").splitlines()[0])

    assert payload["executor_result_status"] == "partial"
    assert payload["executor_ingest_status"] == "accepted_partial"
    assert payload["executor_verify_resume_status"] == "verify_blocked"
    assert payload["executor_changed_files"] == ["src/qa_z/executor_ingest.py"]
    assert payload["next_recommendations"] == ["continue repair"]
