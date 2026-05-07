"""Tests for light repair-session orchestration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
import yaml

from qa_z.artifacts import ArtifactLoadError
from qa_z.cli import main
from qa_z.repair_session import load_repair_session


def python_command(source: str) -> list[str]:
    """Build a cross-platform Python subprocess command."""
    return [sys.executable, "-c", source]


def write_config(tmp_path: Path, checks: list[dict[str, Any]] | None = None) -> None:
    """Write a minimal QA-Z config for repair-session tests."""
    config = {
        "project": {"name": "qa-z-session-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "fail_on_missing_tool": True,
            "checks": checks or [],
        },
        "deep": {"checks": []},
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(tmp_path: Path) -> None:
    """Write a contract with repair constraints."""
    path = tmp_path / "qa" / "contracts" / "contract.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        dedent(
            """
            ---
            title: Session repair contract
            summary: Restore the failing deterministic gate.
            constraints:
              - Keep repair-session orchestration local.
            ---
            # QA Contract: Session repair contract

            ## Acceptance Checks

            - The failed gate passes after repair.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_fast_summary(
    tmp_path: Path,
    run_id: str,
    *,
    check_id: str = "py_test",
    status: str,
    exit_code: int | None,
) -> None:
    """Write a compact fast summary artifact."""
    run_dir = tmp_path / ".qa-z" / "runs" / run_id
    fast_dir = run_dir / "fast"
    fast_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": 2,
        "mode": "fast",
        "contract_path": "qa/contracts/contract.md",
        "project_root": str(tmp_path),
        "status": "failed" if status in {"failed", "error"} else "passed",
        "started_at": "2026-04-14T00:00:00Z",
        "finished_at": "2026-04-14T00:00:01Z",
        "artifact_dir": f".qa-z/runs/{run_id}/fast",
        "checks": [
            {
                "id": check_id,
                "tool": check_id,
                "command": [check_id],
                "kind": "test",
                "status": status,
                "exit_code": exit_code,
                "duration_ms": 1,
                "stdout_tail": "tests/test_app.py::test_example failed",
                "stderr_tail": "",
            }
        ],
    }
    (fast_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_deep_summary(tmp_path: Path, run_id: str) -> None:
    """Write a comparable empty deep summary artifact."""
    deep_dir = tmp_path / ".qa-z" / "runs" / run_id / "deep"
    deep_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": 2,
        "mode": "deep",
        "contract_path": "qa/contracts/contract.md",
        "project_root": str(tmp_path),
        "status": "passed",
        "started_at": "2026-04-14T00:00:00Z",
        "finished_at": "2026-04-14T00:00:01Z",
        "artifact_dir": f".qa-z/runs/{run_id}/deep",
        "checks": [],
    }
    (deep_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_executor_dry_run_summary(
    tmp_path: Path,
    session_id: str,
    *,
    verdict: str,
    verdict_reason: str,
    next_recommendation: str,
    evaluated_attempt_count: int = 1,
    history_signals: list[str] | None = None,
    operator_decision: str = "resolve_verification_blockers",
    operator_summary: str = (
        "A completed executor attempt is still blocked by verification evidence."
    ),
    recommended_actions: list[dict[str, str]] | None = None,
) -> None:
    """Write a compact executor dry-run summary under a repair session."""
    path = (
        tmp_path
        / ".qa-z"
        / "sessions"
        / session_id
        / "executor_results"
        / "dry_run_summary.json"
    )
    signals = history_signals or ["completed_verify_blocked"]
    actions = recommended_actions or [
        {
            "id": "resolve_verification_blockers",
            "summary": (
                "Review verify/summary.json and repair remaining or regressed "
                "blockers before accepting completion."
            ),
        }
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "kind": "qa_z.executor_result_dry_run",
                "schema_version": 1,
                "session_id": session_id,
                "history_path": f".qa-z/sessions/{session_id}/executor_results/history.json",
                "safety_package_id": "qa_z.executor_safety.v1",
                "evaluated_attempt_count": evaluated_attempt_count,
                "latest_attempt_id": "attempt-one",
                "latest_result_status": "completed",
                "latest_ingest_status": "accepted_with_warning",
                "verdict": verdict,
                "verdict_reason": verdict_reason,
                "operator_decision": operator_decision,
                "operator_summary": operator_summary,
                "recommended_actions": actions,
                "history_signals": signals,
                "rule_status_counts": {"clear": 4, "attention": 1, "blocked": 1},
                "rule_evaluations": [],
                "next_recommendation": next_recommendation,
                "report_path": f".qa-z/sessions/{session_id}/executor_results/dry_run_report.md",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def write_executor_result_history(
    tmp_path: Path,
    session_id: str,
    *,
    attempts: list[dict[str, Any]],
) -> None:
    """Write a compact session-local executor-result history artifact."""
    path = (
        tmp_path
        / ".qa-z"
        / "sessions"
        / session_id
        / "executor_results"
        / "history.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "kind": "qa_z.executor_result_history",
                "schema_version": 1,
                "session_id": session_id,
                "updated_at": "2026-04-16T00:00:02Z",
                "attempt_count": len(attempts),
                "latest_attempt_id": attempts[-1]["attempt_id"] if attempts else None,
                "attempts": attempts,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_repair_session_start_creates_manifest_handoff_and_executor_guide(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)

    exit_code = main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    output = capsys.readouterr().out
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    manifest = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    guide = (session_dir / "executor_guide.md").read_text(encoding="utf-8")
    safety_json = json.loads(
        (session_dir / "executor_safety.json").read_text(encoding="utf-8")
    )
    safety_markdown = (session_dir / "executor_safety.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert "qa-z repair-session start: waiting_for_external_repair" in output
    assert manifest["kind"] == "qa_z.repair_session"
    assert manifest["schema_version"] == 1
    assert manifest["session_id"] == "session-one"
    assert manifest["state"] == "waiting_for_external_repair"
    assert manifest["baseline_run_dir"] == ".qa-z/runs/baseline"
    assert manifest["candidate_run_dir"] is None
    assert manifest["handoff_artifacts"]["handoff_json"] == (
        ".qa-z/sessions/session-one/handoff/handoff.json"
    )
    assert manifest["safety_artifacts"]["policy_json"] == (
        ".qa-z/sessions/session-one/executor_safety.json"
    )
    assert manifest["safety_artifacts"]["policy_markdown"] == (
        ".qa-z/sessions/session-one/executor_safety.md"
    )
    assert (session_dir / "handoff" / "packet.json").exists()
    assert (session_dir / "handoff" / "prompt.md").exists()
    assert (session_dir / "handoff" / "handoff.json").exists()
    assert (session_dir / "handoff" / "codex.md").exists()
    assert (session_dir / "handoff" / "claude.md").exists()
    assert "# QA-Z Repair Session Executor Guide" in guide
    assert "does not call Codex or Claude APIs" in guide
    assert "Pre-Live Safety Package" in guide
    assert "python -m qa_z repair-session verify" in guide
    assert safety_json["kind"] == "qa_z.executor_safety"
    assert safety_json["package_id"] == "pre_live_executor_safety_v1"
    assert "verification_required_for_completed" in {
        rule["id"] for rule in safety_json["rules"]
    }
    assert "# QA-Z Pre-Live Executor Safety Package" in safety_markdown


def test_repair_session_load_rejects_manifest_session_dir_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    exit_code = main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    capsys.readouterr()
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    manifest_path = session_dir / "session.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["session_dir"] = ".qa-z/sessions/other-session"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    assert exit_code == 0
    with pytest.raises(ArtifactLoadError, match="session_dir"):
        load_repair_session(tmp_path, "session-one")


def test_repair_session_load_rejects_manifest_session_id_mismatch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    exit_code = main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    capsys.readouterr()
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    manifest_path = session_dir / "session.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["session_id"] = "other-session"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    assert exit_code == 0
    with pytest.raises(ArtifactLoadError, match="session_id"):
        load_repair_session(tmp_path, "session-one")


def test_repair_session_load_rejects_handoff_artifact_outside_session_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    exit_code = main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    capsys.readouterr()
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    manifest_path = session_dir / "session.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["handoff_artifacts"]["handoff_json"] = "qa/contracts/contract.md"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    assert exit_code == 0
    with pytest.raises(ArtifactLoadError, match="handoff_artifacts.handoff_json"):
        load_repair_session(tmp_path, "session-one")


def test_repair_session_start_returns_not_found_for_missing_baseline(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    exit_code = main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/missing",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 4
    assert "qa-z repair-session start: source not found:" in output


def test_repair_session_status_prints_current_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    capsys.readouterr()
    write_executor_dry_run_summary(
        tmp_path,
        "session-one",
        verdict="blocked",
        verdict_reason="completed_attempt_not_verification_clean",
        next_recommendation="resolve verification blocking evidence before another completed attempt",
    )

    exit_code = main(
        [
            "repair-session",
            "status",
            "--path",
            str(tmp_path),
            "--session",
            ".qa-z/sessions/session-one",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "qa-z repair-session: waiting_for_external_repair" in output
    assert "Session: .qa-z/sessions/session-one" in output
    assert "Baseline run: .qa-z/runs/baseline" in output
    assert "Candidate run: none" in output
    assert "Verify: none" in output
    assert (
        "Executor dry-run: blocked (completed_attempt_not_verification_clean)" in output
    )
    assert "Executor dry-run source: materialized" in output
    assert (
        "Executor dry-run diagnostic: A completed executor attempt is still blocked "
        "by verification evidence." in output
    )
    assert (
        "Executor dry-run action: Review verify/summary.json and repair remaining "
        "or regressed blockers before accepting completion." in output
    )


def test_repair_session_status_synthesizes_dry_run_from_history_when_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    capsys.readouterr()
    write_executor_result_history(
        tmp_path,
        "session-one",
        attempts=[
            {
                "attempt_id": "attempt-1",
                "recorded_at": "2026-04-16T00:00:01Z",
                "bridge_id": "bridge-session",
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
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-1.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "recorded_at": "2026-04-16T00:00:02Z",
                "bridge_id": "bridge-session",
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
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-2.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
        ],
    )

    exit_code = main(
        [
            "repair-session",
            "status",
            "--path",
            str(tmp_path),
            "--session",
            ".qa-z/sessions/session-one",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "qa-z repair-session: waiting_for_external_repair" in output
    assert (
        "Executor dry-run: attention_required (manual_retry_review_required)" in output
    )
    assert "Executor dry-run source: history_fallback" in output
    assert (
        "Executor dry-run diagnostic: Repeated partial executor attempts need manual "
        "review before another retry." in output
    )


def test_repair_session_status_json_includes_synthesized_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    capsys.readouterr()
    write_executor_result_history(
        tmp_path,
        "session-one",
        attempts=[
            {
                "attempt_id": "attempt-1",
                "recorded_at": "2026-04-16T00:00:01Z",
                "bridge_id": "bridge-session",
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
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-1.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "recorded_at": "2026-04-16T00:00:02Z",
                "bridge_id": "bridge-session",
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
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-2.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
        ],
    )

    exit_code = main(
        [
            "repair-session",
            "status",
            "--path",
            str(tmp_path),
            "--session",
            ".qa-z/sessions/session-one",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["session_id"] == "session-one"
    assert output["executor_dry_run_verdict"] == "attention_required"
    assert output["executor_dry_run_reason"] == "manual_retry_review_required"
    assert output["executor_dry_run_source"] == "history_fallback"
    assert output["executor_dry_run_attempt_count"] == 2
    assert output["executor_dry_run_history_signals"] == ["repeated_partial_attempts"]
    assert output["executor_dry_run_operator_decision"] == "inspect_partial_attempts"
    assert output["executor_dry_run_operator_summary"] == (
        "Repeated partial executor attempts need manual review before another retry."
    )
    assert output["executor_dry_run_recommended_actions"] == [
        {
            "id": "inspect_partial_attempts",
            "summary": (
                "Review unresolved repair targets across repeated partial attempts "
                "before retrying."
            ),
        }
    ]


def test_repair_session_verify_existing_candidate_writes_outcome(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_fast_summary(tmp_path, "candidate", status="passed", exit_code=0)
    main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    capsys.readouterr()
    write_executor_dry_run_summary(
        tmp_path,
        "session-one",
        verdict="blocked",
        verdict_reason="completed_attempt_not_verification_clean",
        next_recommendation="resolve verification blocking evidence before another completed attempt",
    )

    exit_code = main(
        [
            "repair-session",
            "verify",
            "--path",
            str(tmp_path),
            "--session",
            ".qa-z/sessions/session-one",
            "--candidate-run",
            ".qa-z/runs/candidate",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    manifest = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    summary = json.loads((session_dir / "summary.json").read_text(encoding="utf-8"))
    outcome = (session_dir / "outcome.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert output["kind"] == "qa_z.repair_session_summary"
    assert output["verdict"] == "improved"
    assert manifest["state"] == "completed"
    assert manifest["candidate_run_dir"] == ".qa-z/runs/candidate"
    assert manifest["verify_artifacts"]["summary_json"] == (
        ".qa-z/sessions/session-one/verify/summary.json"
    )
    assert summary["next_recommendation"] == "merge candidate"
    assert summary["executor_dry_run_verdict"] == "blocked"
    assert (
        summary["executor_dry_run_reason"] == "completed_attempt_not_verification_clean"
    )
    assert summary["executor_dry_run_source"] == "materialized"
    assert summary["executor_dry_run_attempt_count"] == 1
    assert summary["executor_dry_run_history_signals"] == ["completed_verify_blocked"]
    assert summary["executor_dry_run_operator_decision"] == (
        "resolve_verification_blockers"
    )
    assert summary["executor_dry_run_operator_summary"] == (
        "A completed executor attempt is still blocked by verification evidence."
    )
    assert summary["executor_dry_run_recommended_actions"] == [
        {
            "id": "resolve_verification_blockers",
            "summary": (
                "Review verify/summary.json and repair remaining or regressed "
                "blockers before accepting completion."
            ),
        }
    ]
    assert (session_dir / "verify" / "summary.json").exists()
    assert (session_dir / "verify" / "compare.json").exists()
    assert (session_dir / "verify" / "report.md").exists()
    assert "# QA-Z Repair Session Outcome" in outcome
    assert "Final verdict: `improved`" in outcome
    assert "Executor dry-run verdict: `blocked`" in outcome
    assert "Dry-run source: `materialized`" in outcome
    assert "Dry-run attempts: `1`" in outcome
    assert "Dry-run history signals: `completed_verify_blocked`" in outcome
    assert "Dry-run operator decision: `resolve_verification_blockers`" in outcome
    assert (
        "Dry-run operator summary: A completed executor attempt is still blocked "
        "by verification evidence." in outcome
    )
    assert "Dry-run recommended actions:" in outcome
    assert (
        "Action `resolve_verification_blockers`: Review verify/summary.json and "
        "repair remaining or regressed blockers before accepting completion." in outcome
    )


def test_repair_session_verify_synthesizes_dry_run_from_history_when_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_fast_summary(tmp_path, "candidate", status="passed", exit_code=0)
    main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    capsys.readouterr()
    write_executor_result_history(
        tmp_path,
        "session-one",
        attempts=[
            {
                "attempt_id": "attempt-1",
                "recorded_at": "2026-04-16T00:00:01Z",
                "bridge_id": "bridge-session",
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
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-1.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
            {
                "attempt_id": "attempt-2",
                "recorded_at": "2026-04-16T00:00:02Z",
                "bridge_id": "bridge-session",
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
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-2.json",
                "ingest_artifact_path": "",
                "ingest_report_path": "",
                "freshness_status": "passed",
                "freshness_reason": None,
                "provenance_status": "passed",
                "provenance_reason": None,
            },
        ],
    )

    exit_code = main(
        [
            "repair-session",
            "verify",
            "--path",
            str(tmp_path),
            "--session",
            ".qa-z/sessions/session-one",
            "--candidate-run",
            ".qa-z/runs/candidate",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    summary = json.loads((session_dir / "summary.json").read_text(encoding="utf-8"))
    outcome = (session_dir / "outcome.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert output["verdict"] == "improved"
    assert summary["executor_dry_run_verdict"] == "attention_required"
    assert summary["executor_dry_run_reason"] == "manual_retry_review_required"
    assert summary["executor_dry_run_source"] == "history_fallback"
    assert summary["executor_dry_run_attempt_count"] == 2
    assert summary["executor_dry_run_history_signals"] == ["repeated_partial_attempts"]
    assert summary["executor_dry_run_operator_summary"] == (
        "Repeated partial executor attempts need manual review before another retry."
    )
    assert "Executor dry-run verdict: `attention_required`" in outcome
    assert "Dry-run source: `history_fallback`" in outcome
    assert "Dry-run attempts: `2`" in outcome
    assert "Dry-run history signals: `repeated_partial_attempts`" in outcome
    assert "Dry-run recommended actions:" in outcome
    assert (
        "Action `inspect_partial_attempts`: Review unresolved repair targets "
        "across repeated partial attempts before retrying." in outcome
    )


def test_repair_session_verify_rerun_creates_candidate_under_session(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(
        tmp_path,
        checks=[{"id": "py_test", "run": python_command(""), "kind": "test"}],
    )
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_deep_summary(tmp_path, "baseline")
    main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
        ]
    )
    capsys.readouterr()

    exit_code = main(
        [
            "repair-session",
            "verify",
            "--path",
            str(tmp_path),
            "--session",
            ".qa-z/sessions/session-one",
            "--rerun",
        ]
    )
    output = capsys.readouterr().out
    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    manifest = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert "qa-z repair-session verify: improved" in output
    assert manifest["state"] == "completed"
    assert manifest["candidate_run_dir"] == ".qa-z/sessions/session-one/candidate"
    assert (session_dir / "candidate" / "fast" / "summary.json").exists()
    assert (session_dir / "candidate" / "deep" / "summary.json").exists()
    assert (session_dir / "candidate" / "review" / "review.md").exists()
    assert (session_dir / "verify" / "summary.json").exists()
    assert (session_dir / "outcome.md").exists()
