"""Tests for executor result contracts and ingest/resume workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
import yaml

from qa_z.autonomy import run_autonomy
from qa_z.cli import main
from qa_z.config import load_config
from qa_z.executor_bridge import create_executor_bridge
from qa_z.executor_ingest import (
    ExecutorResultIngestRejected,
    ingest_executor_result_artifact,
    render_executor_result_ingest_stdout,
    render_ingest_report,
)


NOW = "2026-04-16T00:00:00Z"


def python_command(source: str) -> list[str]:
    """Build a cross-platform Python subprocess command."""
    return [sys.executable, "-c", source]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON object fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_config(tmp_path: Path, checks: list[dict[str, Any]] | None = None) -> None:
    """Write a minimal QA-Z config for executor-result tests."""
    config = {
        "project": {"name": "qa-z-executor-result-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "fail_on_missing_tool": True,
            "checks": checks
            or [
                {
                    "id": "py_test",
                    "run": python_command(""),
                    "kind": "test",
                }
            ],
        },
        "deep": {"checks": []},
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(tmp_path: Path, *, related_files: list[str] | None = None) -> None:
    """Write a contract that repair-session creation can resolve."""
    path = tmp_path / "qa" / "contracts" / "contract.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    files = related_files or ["src/qa_z/executor_result.py"]
    path.write_text(
        dedent(
            f"""
            ---
            title: Executor result contract
            summary: Restore deterministic QA evidence.
            constraints:
              - Keep execution local.
            ---
            # QA Contract: Executor result contract

            ## Related Files

            {chr(10).join(f"- {path}" for path in files)}

            ## Acceptance Checks

            - The candidate run no longer regresses deterministic evidence.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_fast_summary(
    tmp_path: Path,
    run_id: str,
    *,
    status: str,
    exit_code: int | None,
) -> None:
    """Write a compact fast run summary."""
    fast_dir = tmp_path / ".qa-z" / "runs" / run_id / "fast"
    fast_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        fast_dir / "summary.json",
        {
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
                    "id": "py_test",
                    "tool": "pytest",
                    "command": ["pytest"],
                    "kind": "test",
                    "status": status,
                    "exit_code": exit_code,
                    "duration_ms": 1,
                    "stdout_tail": "test failed",
                    "stderr_tail": "",
                }
            ],
        },
    )


def write_deep_summary(tmp_path: Path, run_id: str) -> None:
    """Write a comparable empty deep summary artifact."""
    deep_dir = tmp_path / ".qa-z" / "runs" / run_id / "deep"
    deep_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        deep_dir / "summary.json",
        {
            "schema_version": 2,
            "mode": "deep",
            "contract_path": "qa/contracts/contract.md",
            "project_root": str(tmp_path),
            "status": "passed",
            "started_at": "2026-04-14T00:00:00Z",
            "finished_at": "2026-04-14T00:00:01Z",
            "artifact_dir": f".qa-z/runs/{run_id}/deep",
            "checks": [],
        },
    )


def write_regressed_verify_artifacts(tmp_path: Path) -> None:
    """Seed verification artifacts that identify a baseline run for repair."""
    verify_dir = tmp_path / ".qa-z" / "runs" / "candidate" / "verify"
    write_json(
        verify_dir / "summary.json",
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "repair_improved": False,
            "verdict": "regressed",
            "blocking_before": 0,
            "blocking_after": 1,
            "resolved_count": 0,
            "new_issue_count": 1,
            "regression_count": 1,
            "not_comparable_count": 0,
        },
    )
    write_json(
        verify_dir / "compare.json",
        {
            "kind": "qa_z.verify_compare",
            "schema_version": 1,
            "baseline_run_id": "baseline",
            "candidate_run_id": "candidate",
            "baseline": {
                "run_dir": ".qa-z/runs/baseline",
                "fast_status": "passed",
                "deep_status": None,
            },
            "candidate": {
                "run_dir": ".qa-z/runs/candidate",
                "fast_status": "failed",
                "deep_status": None,
            },
            "verdict": "regressed",
            "fast_checks": {},
            "deep_findings": {},
            "summary": {"regression_count": 1},
        },
    )


def write_executor_result(path: Path, payload: dict[str, Any]) -> None:
    """Write an executor result fixture."""
    write_json(path, payload)


def read_json(path: Path) -> dict[str, Any]:
    """Read a deterministic JSON object fixture."""
    return json.loads(path.read_text(encoding="utf-8"))


def read_history(path: Path) -> dict[str, Any]:
    """Read a deterministic executor-result history artifact."""
    return json.loads(path.read_text(encoding="utf-8"))


def start_session_and_bridge(
    tmp_path: Path,
    capsys,
    *,
    session_id: str = "session-one",
    bridge_id: str = "bridge-session",
) -> tuple[Path, Any]:
    """Create a repair session and executor bridge for ingest tests."""
    start_exit = main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            session_id,
        ]
    )
    capsys.readouterr()
    bridge = create_executor_bridge(
        root=tmp_path,
        from_session=session_id,
        bridge_id=bridge_id,
        now=NOW,
    )
    assert start_exit == 0
    assert bridge.manifest_path.exists()
    session_dir = tmp_path / ".qa-z" / "sessions" / session_id
    manifest = read_json(session_dir / "session.json")
    manifest["created_at"] = NOW
    manifest["updated_at"] = NOW
    write_json(session_dir / "session.json", manifest)
    return session_dir, bridge


def start_loop_bridge(tmp_path: Path, capsys) -> tuple[str, str, Any]:
    """Create an autonomy-backed repair session and bridge."""
    write_fast_summary(tmp_path, "candidate", status="passed", exit_code=0)
    write_regressed_verify_artifacts(tmp_path)
    summary = run_autonomy(
        root=tmp_path,
        config=load_config(tmp_path),
        loops=1,
        count=1,
        now="2026-04-15T00:00:00Z",
    )
    capsys.readouterr()
    loop_id = summary["latest_loop_id"]
    outcome_path = tmp_path / ".qa-z" / "loops" / loop_id / "outcome.json"
    outcome = read_json(outcome_path)
    outcome["live_repository"] = {
        "modified_count": 5,
        "untracked_count": 1,
        "staged_count": 0,
        "runtime_artifact_count": 0,
        "benchmark_result_count": 0,
        "current_branch": "codex/qa-z-bootstrap",
        "current_head": "1234567890abcdef1234567890abcdef12345678",
        "generated_artifact_policy_explicit": True,
        "dirty_area_summary": "source:3, tests:2, docs:1",
    }
    write_json(outcome_path, outcome)
    session_id = f"{loop_id}-verify_regression-candidate"
    bridge = create_executor_bridge(
        root=tmp_path,
        from_loop=loop_id,
        bridge_id="bridge-loop",
        now=NOW,
    )
    assert bridge.manifest_path.exists()
    session_dir = tmp_path / ".qa-z" / "sessions" / session_id
    manifest = read_json(session_dir / "session.json")
    manifest["created_at"] = NOW
    manifest["updated_at"] = NOW
    write_json(session_dir / "session.json", manifest)
    return loop_id, session_id, bridge


def test_executor_result_ingest_reruns_verification_and_updates_session(
    tmp_path: Path, capsys
) -> None:
    write_config(
        tmp_path,
        checks=[{"id": "py_test", "run": python_command(""), "kind": "test"}],
    )
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_deep_summary(tmp_path, "baseline")
    session_dir, _bridge = start_session_and_bridge(tmp_path, capsys)

    result_path = tmp_path / "external-result.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": NOW,
            "status": "completed",
            "summary": "Applied the scoped repair and left unrelated files untouched.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "added",
                    "old_path": None,
                    "summary": "Added result ingest workflow.",
                }
            ],
            "validation": {
                "status": "passed",
                "commands": [["python", "-m", "pytest"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "passed",
                        "exit_code": 0,
                        "summary": "pytest passed locally",
                    }
                ],
            },
            "notes": ["ready for deterministic rerun verification"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    manifest = read_json(session_dir / "session.json")

    assert exit_code == 0
    assert output["kind"] == "qa_z.executor_result_ingest"
    assert output["ingest_status"] == "accepted"
    assert output["result_status"] == "completed"
    assert output["warnings"] == []
    assert output["freshness_check"]["status"] == "passed"
    assert output["provenance_check"]["status"] == "passed"
    assert output["verify_resume_status"] == "ready_for_verify"
    assert "source_self_inspection" not in output
    assert "live_repository" not in output
    assert output["verification_triggered"] is True
    assert output["verification_verdict"] == "improved"
    assert output["session_id"] == "session-one"
    assert (
        output["stored_result_path"]
        == ".qa-z/sessions/session-one/executor_result.json"
    )
    assert (
        output["verify_summary_path"]
        == ".qa-z/sessions/session-one/verify/summary.json"
    )
    assert output["backlog_implications"] == []
    assert (tmp_path / output["ingest_artifact_path"]).exists()
    assert (tmp_path / output["ingest_report_path"]).exists()
    assert manifest["state"] == "completed"
    assert manifest["executor_result_status"] == "completed"
    assert manifest["executor_result_validation_status"] == "passed"
    assert manifest["executor_result_bridge_id"] == "bridge-session"
    assert (
        manifest["executor_result_path"]
        == ".qa-z/sessions/session-one/executor_result.json"
    )
    assert manifest["candidate_run_dir"] == ".qa-z/sessions/session-one/candidate"
    assert (session_dir / "executor_result.json").exists()
    assert (session_dir / "verify" / "summary.json").exists()
    assert (session_dir / "outcome.md").exists()
    history = read_history(session_dir / "executor_results" / "history.json")
    assert history["kind"] == "qa_z.executor_result_history"
    assert history["session_id"] == "session-one"
    assert history["attempt_count"] == 1
    assert history["latest_attempt_id"] == history["attempts"][0]["attempt_id"]
    assert history["attempts"][0]["result_status"] == "completed"
    assert history["attempts"][0]["ingest_status"] == "accepted"
    assert history["attempts"][0]["verification_verdict"] == "improved"
    assert history["attempts"][0]["attempt_path"].endswith(".json")


def test_executor_result_ingest_updates_loop_history_without_verifying(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    loop_id, session_id, _bridge = start_loop_bridge(tmp_path, capsys)

    result_path = tmp_path / "partial-result.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-loop",
            "source_session_id": session_id,
            "source_loop_id": loop_id,
            "created_at": NOW,
            "status": "partial",
            "summary": "Scoped edits were started, but deterministic validation still fails.",
            "verification_hint": "skip",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Started ingest support.",
                }
            ],
            "validation": {
                "status": "failed",
                "commands": [["python", "-m", "pytest"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "failed",
                        "exit_code": 1,
                        "summary": "pytest still fails",
                    }
                ],
            },
            "notes": ["needs another repair loop"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    session_dir = tmp_path / ".qa-z" / "sessions" / session_id
    manifest = read_json(session_dir / "session.json")
    history = json.loads(
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )

    assert exit_code == 0
    assert output["ingest_status"] == "accepted_partial"
    assert output["verification_triggered"] is False
    assert output["result_status"] == "partial"
    assert (
        output["source_self_inspection"] == f".qa-z/loops/{loop_id}/self_inspect.json"
    )
    assert output["source_self_inspection_loop_id"] == loop_id
    assert output["source_self_inspection_generated_at"] == "2026-04-15T00:00:00Z"
    assert output["live_repository"]["modified_count"] == 5
    assert output["live_repository"]["current_branch"] == "codex/qa-z-bootstrap"
    assert (
        output["live_repository"]["current_head"]
        == "1234567890abcdef1234567890abcdef12345678"
    )
    assert output["session_state"] == "candidate_generated"
    assert output["verify_resume_status"] == "verify_blocked"
    assert output["backlog_implications"][0]["category"] == "partial_completion_gap"
    assert output["next_recommendation"] == "continue repair"
    assert manifest["state"] == "candidate_generated"
    assert manifest["executor_result_status"] == "partial"
    assert manifest["verify_dir"] is None
    assert history["loop_id"] == loop_id
    assert history["executor_result_status"] == "partial"
    assert history["executor_validation_status"] == "failed"
    assert history["executor_changed_files"] == ["src/qa_z/executor_result.py"]
    assert history["executor_verification_hint"] == "skip"
    assert history["executor_ingest_status"] == "accepted_partial"
    assert history["executor_verify_resume_status"] == "verify_blocked"
    assert history["executor_result_path"] == (
        f".qa-z/sessions/{session_id}/executor_result.json"
    )
    session_history = read_history(session_dir / "executor_results" / "history.json")
    attempt = session_history["attempts"][0]
    assert (
        attempt["source_self_inspection"] == f".qa-z/loops/{loop_id}/self_inspect.json"
    )
    assert attempt["source_self_inspection_loop_id"] == loop_id
    assert attempt["source_self_inspection_generated_at"] == "2026-04-15T00:00:00Z"
    assert attempt["live_repository"]["dirty_area_summary"] == (
        "source:3, tests:2, docs:1"
    )
    assert attempt["live_repository"]["current_branch"] == "codex/qa-z-bootstrap"
    assert (
        attempt["live_repository"]["current_head"]
        == "1234567890abcdef1234567890abcdef12345678"
    )
    ingest_report = (tmp_path / output["ingest_report_path"]).read_text(
        encoding="utf-8"
    )
    assert "Live Repository Context" in ingest_report
    assert f"Source self-inspection: `.qa-z/loops/{loop_id}/self_inspect.json`" in (
        ingest_report
    )
    assert f"Source loop: `{loop_id}`" in ingest_report
    assert "Source generated at: `2026-04-15T00:00:00Z`" in ingest_report
    assert (
        "modified=5; untracked=1; staged=0; runtime_artifacts=0; "
        "benchmark_results=0; dirty_benchmark_results=0; release_evidence=0; "
        "generated_policy=true; "
        "branch=codex/qa-z-bootstrap; "
        "head=1234567890abcdef1234567890abcdef12345678; "
        "areas=source:3, tests:2, docs:1" in ingest_report
    )


def test_executor_result_ingest_stdout_reports_source_context(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    loop_id, session_id, _bridge = start_loop_bridge(tmp_path, capsys)

    result_path = tmp_path / "partial-result.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-loop",
            "source_session_id": session_id,
            "source_loop_id": loop_id,
            "created_at": NOW,
            "status": "partial",
            "summary": "Scoped edits were started, but deterministic validation still fails.",
            "verification_hint": "skip",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Started ingest support.",
                }
            ],
            "validation": {
                "status": "failed",
                "commands": [["python", "-m", "pytest"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "failed",
                        "exit_code": 1,
                        "summary": "pytest still fails",
                    }
                ],
            },
            "notes": ["needs another repair loop"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Ingest report: .qa-z/executor-results/" in output
    assert "ingest_report.md" in output
    assert f"Source self-inspection: .qa-z/loops/{loop_id}/self_inspect.json" in output
    assert f"Source loop: {loop_id}" in output
    assert "Source generated at: 2026-04-15T00:00:00Z" in output
    assert (
        "Live repository: modified=5; untracked=1; staged=0; runtime_artifacts=0; "
        "benchmark_results=0; dirty_benchmark_results=0; release_evidence=0; "
        "generated_policy=true; "
        "branch=codex/qa-z-bootstrap; "
        "head=1234567890abcdef1234567890abcdef12345678; "
        "areas=source:3, tests:2, docs:1" in output
    )
    assert "Freshness: passed" in output
    assert "Provenance: passed" in output
    assert "Backlog implications: partial_completion_gap" in output


def test_executor_result_ingest_human_surfaces_keep_partial_source_context() -> None:
    summary: dict[str, Any] = {
        "result_id": "partial-source",
        "bridge_id": "bridge-partial-source",
        "session_id": "session-partial-source",
        "result_status": "partial",
        "ingest_status": "accepted_partial",
        "stored_result_path": None,
        "ingest_report_path": ".qa-z/executor-results/partial-source/ingest_report.md",
        "verify_resume_status": "verify_blocked",
        "verification_verdict": None,
        "source_self_inspection": ".qa-z/loops/loop-source/self_inspect.json",
        "source_self_inspection_loop_id": "loop-source",
        "source_self_inspection_generated_at": "2026-04-16T00:00:00Z",
        "freshness_check": {"status": "passed", "details": []},
        "provenance_check": {"status": "passed", "details": []},
        "warnings": [],
        "backlog_implications": [],
        "next_recommendation": "continue repair",
    }

    stdout = render_executor_result_ingest_stdout(summary)
    report = render_ingest_report(summary)

    assert "Source self-inspection: .qa-z/loops/loop-source/self_inspect.json" in stdout
    assert "Source loop: loop-source" in stdout
    assert "Source generated at: 2026-04-16T00:00:00Z" in stdout
    assert "Live repository:" not in stdout
    assert "## Source Context" in report
    assert "Source self-inspection: `.qa-z/loops/loop-source/self_inspect.json`" in (
        report
    )
    assert "Source loop: `loop-source`" in report
    assert "Source generated at: `2026-04-16T00:00:00Z`" in report
    assert "## Live Repository Context" not in report


def test_executor_result_ingest_human_uses_unknown_for_missing_source_path() -> None:
    summary: dict[str, Any] = {
        "result_id": "partial-source-path",
        "bridge_id": "bridge-partial-source-path",
        "session_id": "session-partial-source-path",
        "result_status": "partial",
        "ingest_status": "accepted_partial",
        "stored_result_path": None,
        "ingest_report_path": (
            ".qa-z/executor-results/partial-source-path/ingest_report.md"
        ),
        "verify_resume_status": "verify_blocked",
        "verification_verdict": None,
        "source_self_inspection_loop_id": "loop-source-only",
        "freshness_check": {"status": "passed", "details": []},
        "provenance_check": {"status": "passed", "details": []},
        "warnings": [],
        "backlog_implications": [],
        "next_recommendation": "continue repair",
    }

    stdout = render_executor_result_ingest_stdout(summary)
    report = render_ingest_report(summary)

    assert "Source self-inspection: unknown" in stdout
    assert "Source loop: loop-source-only" in stdout
    assert "Source generated at: unknown" in stdout
    assert "Source self-inspection: `unknown`" in report
    assert "Source loop: `loop-source-only`" in report
    assert "Source generated at: `unknown`" in report
    assert "`None`" not in report


def test_executor_result_ingest_rejects_unrelated_changed_files(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, related_files=["src/qa_z/executor_result.py"])
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    session_dir, _bridge = start_session_and_bridge(tmp_path, capsys)

    result_path = tmp_path / "external-result-unrelated.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": NOW,
            "status": "completed",
            "summary": "Edited an unrelated docs file while attempting the repair.",
            "verification_hint": "skip",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "docs/README.md",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Unrelated docs edit.",
                }
            ],
            "validation": {
                "status": "not_run",
                "commands": [],
                "results": [],
            },
            "notes": ["should be rejected as unrelated scope"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    manifest = read_json(session_dir / "session.json")

    assert exit_code == 2
    assert output["ingest_status"] == "rejected_invalid"
    assert output["verify_resume_status"] == "verify_blocked"
    assert output["stored_result_path"] is None
    assert output["warnings"] == []
    assert any(
        "outside the bridge affected_files" in detail
        for detail in output["provenance_check"]["details"]
    )
    assert (session_dir / "executor_result.json").exists() is False
    assert manifest["executor_result_status"] is None
    assert (tmp_path / output["ingest_artifact_path"]).exists()
    history = read_history(session_dir / "executor_results" / "history.json")
    assert history["attempt_count"] == 1
    assert history["attempts"][0]["ingest_status"] == "rejected_invalid"
    assert history["attempts"][0]["result_status"] == "completed"
    assert history["attempts"][0]["verify_resume_status"] == "verify_blocked"


def test_executor_result_ingest_rejects_result_older_than_bridge(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    session_dir, bridge = start_session_and_bridge(tmp_path, capsys)
    bridge_manifest = read_json(bridge.manifest_path)
    assert bridge_manifest["created_at"] == NOW

    result_path = tmp_path / "older-than-bridge.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": "2026-04-15T23:59:59Z",
            "status": "completed",
            "summary": "Claims a completed repair from before the bridge existed.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Touched ingest handling.",
                }
            ],
            "validation": {"status": "passed", "commands": [], "results": []},
            "notes": ["should be rejected as impossible provenance"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["ingest_status"] == "rejected_invalid"
    assert output["freshness_check"]["status"] == "failed"
    assert output["freshness_check"]["reason"] == "result_before_bridge"
    assert output["verify_resume_status"] == "verify_blocked"
    assert read_json(session_dir / "session.json")["executor_result_status"] is None
    assert (session_dir / "executor_result.json").exists() is False


def test_executor_result_ingest_rejects_stale_result_when_session_is_newer(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    session_dir, bridge = start_session_and_bridge(tmp_path, capsys)
    manifest = read_json(session_dir / "session.json")
    manifest["updated_at"] = "2026-04-16T01:00:00Z"
    write_json(session_dir / "session.json", manifest)
    assert read_json(bridge.manifest_path)["created_at"] == NOW

    result_path = tmp_path / "stale-result.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": "2026-04-16T00:30:00Z",
            "status": "completed",
            "summary": "Completed before a newer session update moved the target.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Touched ingest handling.",
                }
            ],
            "validation": {"status": "passed", "commands": [], "results": []},
            "notes": ["should be rejected as stale"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["ingest_status"] == "rejected_stale"
    assert output["freshness_check"]["status"] == "failed"
    assert output["freshness_check"]["reason"] == "session_newer_than_result"
    assert output["verify_resume_status"] == "stale_result"
    assert output["backlog_implications"][0]["category"] == "evidence_freshness_gap"
    assert (session_dir / "executor_result.json").exists() is False


def test_executor_result_ingest_rejects_result_from_future_relative_to_ingest_time(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    session_dir, _bridge = start_session_and_bridge(tmp_path, capsys)

    result_path = tmp_path / "future-result.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": "2026-04-16T00:10:00Z",
            "status": "completed",
            "summary": "Claims completion from a timestamp after ingest began.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Touched ingest handling.",
                }
            ],
            "validation": {"status": "passed", "commands": [], "results": []},
            "notes": ["should be rejected as future-dated evidence"],
        },
    )

    with pytest.raises(ExecutorResultIngestRejected) as exc_info:
        ingest_executor_result_artifact(
            root=tmp_path,
            config=load_config(tmp_path),
            result_path=result_path,
            now=NOW,
        )
    output = exc_info.value.outcome.summary

    assert output["ingest_status"] == "rejected_invalid"
    assert output["freshness_check"]["status"] == "failed"
    assert output["freshness_check"]["reason"] == "result_from_future"
    assert output["freshness_check"]["ingested_at"] == NOW
    assert output["verify_resume_status"] == "verify_blocked"
    assert output["next_recommendation"] == "fix executor result timestamps"
    assert output["backlog_implications"][0]["category"] == "evidence_freshness_gap"
    assert read_json(session_dir / "session.json")["executor_result_status"] is None
    assert (session_dir / "executor_result.json").exists() is False


def test_executor_result_ingest_rejects_loop_provenance_mismatch(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    loop_id, session_id, _bridge = start_loop_bridge(tmp_path, capsys)

    result_path = tmp_path / "wrong-loop.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-loop",
            "source_session_id": session_id,
            "source_loop_id": f"{loop_id}-wrong",
            "created_at": NOW,
            "status": "completed",
            "summary": "Claims to belong to a different autonomy loop.",
            "verification_hint": "skip",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Touched ingest handling.",
                }
            ],
            "validation": {"status": "passed", "commands": [], "results": []},
            "notes": ["should be rejected as a mismatch"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["ingest_status"] == "rejected_mismatch"
    assert output["provenance_check"]["status"] == "failed"
    assert output["provenance_check"]["reason"] == "source_loop_mismatch"
    assert output["verify_resume_status"] == "mismatch_detected"
    assert (
        output["backlog_implications"][0]["recommendation"] == "audit_executor_contract"
    )


def test_executor_result_ingest_blocks_verify_for_completed_without_changed_files(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    session_dir, _bridge = start_session_and_bridge(tmp_path, capsys)

    result_path = tmp_path / "completed-without-changes.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": NOW,
            "status": "completed",
            "summary": "Claims completion without recording any changed files.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [],
            "validation": {"status": "passed", "commands": [], "results": []},
            "notes": ["suspicious completed result"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    manifest = read_json(session_dir / "session.json")

    assert exit_code == 0
    assert output["ingest_status"] == "accepted_with_warning"
    assert "completed_without_changed_files" in output["warnings"]
    assert output["verify_resume_status"] == "verify_blocked"
    assert output["verification_triggered"] is False
    assert manifest["executor_result_status"] == "completed"
    assert manifest["verify_dir"] is None


def test_executor_result_ingest_blocks_verify_for_validation_summary_conflict(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    session_dir, _bridge = start_session_and_bridge(tmp_path, capsys)

    result_path = tmp_path / "validation-conflict.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": NOW,
            "status": "completed",
            "summary": "Claims a passing validation summary even though pytest failed.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Touched ingest handling.",
                }
            ],
            "validation": {
                "status": "passed",
                "commands": [["python", "-m", "pytest"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "failed",
                        "exit_code": 1,
                        "summary": "pytest still fails",
                    }
                ],
            },
            "notes": ["validation evidence should block optimistic verify resume"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    manifest = read_json(session_dir / "session.json")

    assert exit_code == 0
    assert output["ingest_status"] == "accepted_with_warning"
    assert "validation_summary_conflicts_with_results" in output["warnings"]
    assert output["verify_resume_status"] == "verify_blocked"
    assert output["verification_triggered"] is False
    assert output["next_recommendation"] == "inspect executor result warnings"
    assert output["backlog_implications"][0]["category"] == "workflow_gap"
    assert manifest["executor_result_status"] == "completed"
    assert manifest["verify_dir"] is None


def test_executor_result_ingest_accepts_no_op_with_warning_when_explanation_is_missing(
    tmp_path: Path, capsys
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    session_dir, _bridge = start_session_and_bridge(tmp_path, capsys)

    result_path = tmp_path / "no-op-without-notes.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": NOW,
            "status": "no_op",
            "summary": "The executor reports that the task did not need edits.",
            "verification_hint": "skip",
            "candidate_run_dir": None,
            "changed_files": [],
            "validation": {"status": "not_run", "commands": [], "results": []},
            "notes": [],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["ingest_status"] == "accepted_no_op"
    assert "no_op_without_explanation" in output["warnings"]
    assert output["verify_resume_status"] == "verify_blocked"
    assert output["backlog_implications"][0]["category"] == "no_op_safeguard_gap"
    assert read_json(session_dir / "session.json")["executor_result_status"] == "no_op"


def test_executor_result_ingest_warns_when_bridge_timestamp_is_missing(
    tmp_path: Path, capsys
) -> None:
    write_config(
        tmp_path,
        checks=[{"id": "py_test", "run": python_command(""), "kind": "test"}],
    )
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_deep_summary(tmp_path, "baseline")
    session_dir, bridge = start_session_and_bridge(tmp_path, capsys)
    manifest = read_json(bridge.manifest_path)
    manifest["created_at"] = ""
    write_json(bridge.manifest_path, manifest)

    result_path = tmp_path / "missing-bridge-timestamp.json"
    write_executor_result(
        result_path,
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": NOW,
            "status": "completed",
            "summary": "Completed result with missing bridge freshness metadata.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/qa_z/executor_result.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Touched ingest handling.",
                }
            ],
            "validation": {"status": "passed", "commands": [], "results": []},
            "notes": ["bridge timestamp should trigger a warning"],
        },
    )

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["ingest_status"] == "accepted_with_warning"
    assert output["freshness_check"]["status"] == "warning"
    assert "missing_bridge_created_at" in output["warnings"]
    assert output["verify_resume_status"] == "ingested_with_warning"
    assert output["verification_triggered"] is True
    assert read_json(session_dir / "session.json")["state"] == "completed"
