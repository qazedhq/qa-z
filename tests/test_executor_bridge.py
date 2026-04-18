"""Tests for executor bridge packaging."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
import yaml

from qa_z.cli import main
from qa_z.config import load_config
from qa_z.executor_bridge import (
    ExecutorBridgeError,
    create_executor_bridge,
    render_bridge_stdout,
)
from qa_z.repair_session import create_repair_session


NOW = "2026-04-15T00:00:00Z"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_config(tmp_path: Path) -> None:
    """Write a minimal QA-Z config for bridge tests."""
    config = {
        "project": {"name": "qa-z-bridge-test", "languages": ["python"]},
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
    """Write a contract that repair-session creation can resolve."""
    path = tmp_path / "qa" / "contracts" / "contract.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        dedent(
            """
            ---
            title: Bridge repair contract
            summary: Restore deterministic QA evidence.
            constraints:
              - Keep executor bridge work local.
            ---
            # QA Contract: Bridge repair contract

            ## Acceptance Checks

            - The candidate run resolves the baseline failure.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_fast_summary(tmp_path: Path, run_id: str) -> None:
    """Write a compact failing fast run summary."""
    fast_dir = tmp_path / ".qa-z" / "runs" / run_id / "fast"
    fast_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        fast_dir / "summary.json",
        {
            "schema_version": 2,
            "mode": "fast",
            "contract_path": "qa/contracts/contract.md",
            "project_root": str(tmp_path),
            "status": "failed",
            "started_at": "2026-04-14T00:00:00Z",
            "finished_at": "2026-04-14T00:00:01Z",
            "artifact_dir": f".qa-z/runs/{run_id}/fast",
            "checks": [
                {
                    "id": "py_test",
                    "tool": "pytest",
                    "command": ["pytest"],
                    "kind": "test",
                    "status": "failed",
                    "exit_code": 1,
                    "duration_ms": 1,
                    "stdout_tail": "test failed",
                    "stderr_tail": "",
                }
            ],
        },
    )


def prepare_session(tmp_path: Path) -> None:
    """Create a repair session fixture."""
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline")
    create_repair_session(
        root=tmp_path,
        config=load_config(tmp_path),
        baseline_run=".qa-z/runs/baseline",
        session_id="session-one",
        now=NOW,
    )


def write_loop_outcome(tmp_path: Path) -> None:
    """Write a loop outcome that points at the prepared repair session."""
    path = tmp_path / ".qa-z" / "loops" / "loop-one" / "outcome.json"
    write_json(
        path,
        {
            "kind": "qa_z.autonomy_outcome",
            "schema_version": 1,
            "loop_id": "loop-one",
            "generated_at": NOW,
            "state": "awaiting_repair",
            "selected_task_ids": ["task-one"],
            "actions_prepared": [
                {
                    "type": "repair_session",
                    "task_id": "task-one",
                    "session_dir": ".qa-z/sessions/session-one",
                }
            ],
            "next_recommendations": ["repair the prepared session"],
            "artifacts": {"outcome": ".qa-z/loops/loop-one/outcome.json"},
        },
    )


def test_executor_bridge_from_session_packages_manifest_guides_and_inputs(
    tmp_path: Path,
) -> None:
    prepare_session(tmp_path)

    result = create_executor_bridge(
        root=tmp_path,
        from_session="session-one",
        bridge_id="bridge-one",
        now=NOW,
    )

    bridge_dir = tmp_path / ".qa-z" / "executor" / "bridge-one"
    manifest = json.loads((bridge_dir / "bridge.json").read_text(encoding="utf-8"))
    guide = (bridge_dir / "executor_guide.md").read_text(encoding="utf-8")
    codex = (bridge_dir / "codex.md").read_text(encoding="utf-8")
    claude = (bridge_dir / "claude.md").read_text(encoding="utf-8")

    assert result.manifest_path == bridge_dir / "bridge.json"
    assert manifest["kind"] == "qa_z.executor_bridge"
    assert manifest["schema_version"] == 1
    assert manifest["bridge_id"] == "bridge-one"
    assert manifest["status"] == "ready_for_external_executor"
    assert manifest["source_session_id"] == "session-one"
    assert manifest["source_loop_id"] is None
    assert manifest["baseline_run"] == ".qa-z/runs/baseline"
    assert manifest["session_dir"] == ".qa-z/sessions/session-one"
    assert manifest["handoff_dir"] == ".qa-z/sessions/session-one/handoff"
    assert manifest["inputs"]["session"] == (
        ".qa-z/executor/bridge-one/inputs/session.json"
    )
    assert manifest["inputs"]["handoff"] == (
        ".qa-z/executor/bridge-one/inputs/handoff.json"
    )
    assert manifest["handoff_paths"]["codex_markdown"] == (
        ".qa-z/sessions/session-one/handoff/codex.md"
    )
    assert manifest["validation_commands"] == [
        [
            "python",
            "-m",
            "qa_z",
            "repair-session",
            "verify",
            "--session",
            ".qa-z/sessions/session-one",
            "--candidate-run",
            "<candidate-run>",
        ]
    ]
    assert manifest["return_contract"]["expected_next_step"] == (
        "run repair-session verify after external repair"
    )
    assert "do not call Codex or Claude APIs from QA-Z" in manifest["non_goals"]
    assert (bridge_dir / "inputs" / "session.json").exists()
    assert (bridge_dir / "inputs" / "handoff.json").exists()
    assert "# QA-Z External Executor Bridge" in guide
    assert "Return Contract" in guide
    assert "python -m qa_z repair-session verify" in guide
    assert "QA-Z Executor Bridge for Codex" in codex
    assert "Bridge id: `bridge-one`" in codex
    assert "QA-Z Executor Bridge for Claude" in claude
    assert "Bridge id: `bridge-one`" in claude


def test_executor_bridge_from_loop_copies_loop_outcome(tmp_path: Path) -> None:
    prepare_session(tmp_path)
    write_loop_outcome(tmp_path)

    create_executor_bridge(
        root=tmp_path,
        from_loop="loop-one",
        bridge_id="bridge-one",
        now=NOW,
    )

    bridge_dir = tmp_path / ".qa-z" / "executor" / "bridge-one"
    manifest = json.loads((bridge_dir / "bridge.json").read_text(encoding="utf-8"))

    assert manifest["source_loop_id"] == "loop-one"
    assert manifest["source_session_id"] == "session-one"
    assert manifest["selected_task_ids"] == ["task-one"]
    assert manifest["inputs"]["autonomy_outcome"] == (
        ".qa-z/executor/bridge-one/inputs/autonomy_outcome.json"
    )
    assert (bridge_dir / "inputs" / "autonomy_outcome.json").exists()


def test_executor_bridge_rejects_existing_bridge_dir(tmp_path: Path) -> None:
    prepare_session(tmp_path)
    create_executor_bridge(
        root=tmp_path,
        from_session="session-one",
        bridge_id="bridge-one",
        now=NOW,
    )

    with pytest.raises(ExecutorBridgeError, match="already exists"):
        create_executor_bridge(
            root=tmp_path,
            from_session="session-one",
            bridge_id="bridge-one",
            now=NOW,
        )


def test_executor_bridge_cli_outputs_json_and_human_summary(
    tmp_path: Path, capsys
) -> None:
    prepare_session(tmp_path)

    json_exit = main(
        [
            "executor-bridge",
            "--path",
            str(tmp_path),
            "--from-session",
            "session-one",
            "--bridge-id",
            "bridge-json",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    human_exit = main(
        [
            "executor-bridge",
            "--path",
            str(tmp_path),
            "--from-session",
            "session-one",
            "--bridge-id",
            "bridge-human",
        ]
    )
    output = capsys.readouterr().out

    assert json_exit == 0
    assert payload["bridge_id"] == "bridge-json"
    assert human_exit == 0
    assert "qa-z executor-bridge: ready_for_external_executor" in output
    assert "Bridge: .qa-z/executor/bridge-human" in output
    assert "Verify: python -m qa_z repair-session verify" in output


def test_render_bridge_stdout_includes_return_contract(tmp_path: Path) -> None:
    prepare_session(tmp_path)
    result = create_executor_bridge(
        root=tmp_path,
        from_session="session-one",
        bridge_id="bridge-one",
        now=NOW,
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    output = render_bridge_stdout(manifest)

    assert "qa-z executor-bridge: ready_for_external_executor" in output
    assert "Return: run repair-session verify after external repair" in output
