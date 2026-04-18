"""Tests for local repair-session workflow."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml

from qa_z.cli import main
from qa_z.config import load_config
from qa_z.repair_session import (
    create_repair_session,
    load_repair_session,
    render_session_status,
    session_status_json,
    verify_repair_session,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_config(tmp_path: Path) -> None:
    config = {
        "project": {"name": "qa-z-session-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "fail_on_missing_tool": True,
            "checks": [
                {"id": "py_test", "run": [sys.executable, "-c", ""], "kind": "test"}
            ],
        },
        "deep": {"checks": []},
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(tmp_path: Path) -> None:
    path = tmp_path / "qa" / "contracts" / "contract.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        dedent(
            """
            ---
            title: Repair session contract
            summary: Restore deterministic QA evidence.
            constraints:
              - Keep repair local and evidence-backed.
            ---
            # QA Contract: Repair session contract

            ## Acceptance Checks

            - The candidate run resolves the baseline failure.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_fast_summary(
    tmp_path: Path, run_id: str, *, status: str, exit_code: int | None
) -> None:
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
                    "stdout_tail": "",
                    "stderr_tail": "",
                }
            ],
        },
    )


def test_repair_session_start_creates_manifest_handoff_and_guide(
    tmp_path: Path,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    config = load_config(tmp_path)

    result = create_repair_session(
        root=tmp_path,
        config=config,
        baseline_run=".qa-z/runs/baseline",
        session_id="session-one",
    )

    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    manifest = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    guide = (session_dir / "executor_guide.md").read_text(encoding="utf-8")

    assert result.session.session_id == "session-one"
    assert manifest["kind"] == "qa_z.repair_session"
    assert manifest["state"] == "waiting_for_external_repair"
    assert manifest["baseline_run"] == ".qa-z/runs/baseline"
    assert manifest["handoff_dir"] == ".qa-z/sessions/session-one/handoff"
    assert (session_dir / "handoff" / "packet.json").exists()
    assert (session_dir / "handoff" / "handoff.json").exists()
    assert (session_dir / "handoff" / "codex.md").exists()
    assert (session_dir / "handoff" / "claude.md").exists()
    assert "# QA-Z Repair Session Guide" in guide
    assert "python -m qa_z repair-session verify" in guide


def test_repair_session_verify_candidate_updates_manifest_and_outcome(
    tmp_path: Path,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_fast_summary(tmp_path, "candidate", status="passed", exit_code=0)
    config = load_config(tmp_path)
    create_repair_session(
        root=tmp_path,
        config=config,
        baseline_run=".qa-z/runs/baseline",
        session_id="session-one",
    )

    result = verify_repair_session(
        root=tmp_path,
        config=config,
        session_ref="session-one",
        candidate_run=".qa-z/runs/candidate",
    )

    session_dir = tmp_path / ".qa-z" / "sessions" / "session-one"
    manifest = json.loads((session_dir / "session.json").read_text(encoding="utf-8"))
    summary = json.loads((session_dir / "summary.json").read_text(encoding="utf-8"))
    outcome = (session_dir / "outcome.md").read_text(encoding="utf-8")

    assert result.comparison.verdict == "improved"
    assert manifest["state"] == "verification_complete"
    assert manifest["candidate_run"] == ".qa-z/runs/candidate"
    assert (
        manifest["verify_summary_path"]
        == ".qa-z/sessions/session-one/verify/summary.json"
    )
    assert summary["kind"] == "qa_z.repair_session_summary"
    assert summary["verdict"] == "improved"
    assert summary["resolved_count"] == 1
    assert "# QA-Z Repair Session Outcome" in outcome
    assert "Verdict: `improved`" in outcome


def test_repair_session_status_json_and_human_output(tmp_path: Path) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    config = load_config(tmp_path)
    create_repair_session(
        root=tmp_path,
        config=config,
        baseline_run=".qa-z/runs/baseline",
        session_id="session-one",
    )

    session = load_repair_session(tmp_path, "session-one")
    status_json = json.loads(session_status_json(session))
    output = render_session_status(session)

    assert status_json["session_id"] == "session-one"
    assert status_json["state"] == "waiting_for_external_repair"
    assert "Repair session: session-one" in output
    assert "State: waiting_for_external_repair" in output


def test_repair_session_cli_start_status_and_verify(tmp_path: Path, capsys) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_fast_summary(tmp_path, "candidate", status="passed", exit_code=0)

    start_exit = main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-one",
            "--json",
        ]
    )
    start_output = json.loads(capsys.readouterr().out)
    status_exit = main(
        [
            "repair-session",
            "status",
            "--path",
            str(tmp_path),
            "--session",
            "session-one",
            "--json",
        ]
    )
    status_output = json.loads(capsys.readouterr().out)
    verify_exit = main(
        [
            "repair-session",
            "verify",
            "--path",
            str(tmp_path),
            "--session",
            "session-one",
            "--candidate-run",
            ".qa-z/runs/candidate",
            "--json",
        ]
    )
    verify_output = json.loads(capsys.readouterr().out)

    assert start_exit == 0
    assert start_output["session_id"] == "session-one"
    assert status_exit == 0
    assert status_output["state"] == "waiting_for_external_repair"
    assert verify_exit == 0
    assert verify_output["verdict"] == "improved"
