"""Tests for external executor bridge packaging."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
import yaml

from qa_z.cli import main
from qa_z.artifacts import ArtifactSourceNotFound
from qa_z.config import load_config
from qa_z.executor_bridge_context import copy_input
from qa_z.executor_bridge import (
    ExecutorBridgeError,
    create_executor_bridge,
)
from qa_z.executor_result import PLACEHOLDER_SUMMARY
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS
from qa_z.autonomy import run_autonomy


NOW = "2026-04-15T00:00:00Z"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON object fixture."""
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
                {
                    "id": "py_test",
                    "run": [sys.executable, "-c", ""],
                    "kind": "test",
                }
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


def prepare_autonomy_session(tmp_path: Path) -> tuple[str, str]:
    """Create an autonomy loop that prepares a repair session."""
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_fast_summary(tmp_path, "candidate", status="passed", exit_code=0)
    write_regressed_verify_artifacts(tmp_path)
    run_autonomy(root=tmp_path, config=load_config(tmp_path), loops=1, count=1, now=NOW)
    loop_id = "loop-20260415-000000-01"
    session_id = f"{loop_id}-verify_regression-candidate"
    outcome_path = tmp_path / ".qa-z" / "loops" / loop_id / "outcome.json"
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
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
    return loop_id, session_id


def test_executor_bridge_from_loop_packages_manifest_guides_and_inputs(
    tmp_path: Path,
) -> None:
    loop_id, session_id = prepare_autonomy_session(tmp_path)

    result = create_executor_bridge(
        root=tmp_path,
        from_loop=loop_id,
        bridge_id="bridge-one",
        now=NOW,
    )

    bridge_dir = tmp_path / ".qa-z" / "executor" / "bridge-one"
    manifest = json.loads((bridge_dir / "bridge.json").read_text(encoding="utf-8"))
    guide = (bridge_dir / "executor_guide.md").read_text(encoding="utf-8")
    codex = (bridge_dir / "codex.md").read_text(encoding="utf-8")
    claude = (bridge_dir / "claude.md").read_text(encoding="utf-8")
    result_template = json.loads(
        (bridge_dir / "result_template.json").read_text(encoding="utf-8")
    )
    safety_json = json.loads(
        (bridge_dir / "inputs" / "executor_safety.json").read_text(encoding="utf-8")
    )
    safety_markdown = (bridge_dir / "inputs" / "executor_safety.md").read_text(
        encoding="utf-8"
    )

    assert result.manifest_path == bridge_dir / "bridge.json"
    assert manifest["kind"] == "qa_z.executor_bridge"
    assert manifest["schema_version"] == 1
    assert manifest["bridge_id"] == "bridge-one"
    assert manifest["status"] == "ready_for_external_executor"
    assert manifest["source_loop_id"] == loop_id
    assert manifest["source_session_id"] == session_id
    assert (
        manifest["source_self_inspection"] == f".qa-z/loops/{loop_id}/self_inspect.json"
    )
    assert manifest["source_self_inspection_loop_id"] == loop_id
    assert manifest["source_self_inspection_generated_at"] == NOW
    assert manifest["live_repository"]["modified_count"] == 5
    assert manifest["live_repository"]["current_branch"] == "codex/qa-z-bootstrap"
    assert (
        manifest["live_repository"]["current_head"]
        == "1234567890abcdef1234567890abcdef12345678"
    )
    assert manifest["prepared_action_type"] == "repair_session"
    assert manifest["baseline_run_dir"] == ".qa-z/runs/baseline"
    assert manifest["session_dir"] == f".qa-z/sessions/{session_id}"
    assert (
        manifest["handoff_path"] == f".qa-z/sessions/{session_id}/handoff/handoff.json"
    )
    assert manifest["inputs"]["autonomy_outcome"] == (
        ".qa-z/executor/bridge-one/inputs/autonomy_outcome.json"
    )
    assert (
        manifest["inputs"]["session"] == ".qa-z/executor/bridge-one/inputs/session.json"
    )
    assert (
        manifest["inputs"]["handoff"] == ".qa-z/executor/bridge-one/inputs/handoff.json"
    )
    assert (
        manifest["inputs"]["executor_safety_json"]
        == ".qa-z/executor/bridge-one/inputs/executor_safety.json"
    )
    assert (
        manifest["inputs"]["executor_safety_markdown"]
        == ".qa-z/executor/bridge-one/inputs/executor_safety.md"
    )
    assert manifest["validation_commands"] == [
        [
            "python",
            "-m",
            "qa_z",
            "repair-session",
            "verify",
            "--session",
            f".qa-z/sessions/{session_id}",
            "--rerun",
        ]
    ]
    assert manifest["return_contract"]["expected_next_step"] == (
        "run repair-session verify after edits"
    )
    assert manifest["return_contract"]["expected_result_artifact"] == (
        ".qa-z/executor/bridge-one/result.json"
    )
    assert manifest["return_contract"]["verification_hint_default"] == "rerun"
    assert manifest["safety_package"]["package_id"] == "pre_live_executor_safety_v1"
    assert manifest["safety_package"]["status"] == "pre_live_only"
    expected_rule_count = len(EXECUTOR_SAFETY_RULE_IDS)
    assert manifest["safety_package"]["rule_ids"] == list(EXECUTOR_SAFETY_RULE_IDS)
    assert manifest["safety_package"]["rule_count"] == expected_rule_count
    assert "do not perform unrelated refactors" in manifest["non_goals"]
    assert (bridge_dir / "inputs" / "autonomy_outcome.json").exists()
    assert (bridge_dir / "inputs" / "session.json").exists()
    assert (bridge_dir / "inputs" / "handoff.json").exists()
    assert (bridge_dir / "inputs" / "executor_safety.json").exists()
    assert (bridge_dir / "inputs" / "executor_safety.md").exists()
    assert result_template["kind"] == "qa_z.executor_result"
    assert result_template["bridge_id"] == "bridge-one"
    assert result_template["source_session_id"] == session_id
    assert result_template["verification_hint"] == "rerun"
    assert "changed_files" in result_template
    assert "Why This Work Was Selected" in guide
    assert "Live Repository Context" in guide
    assert (
        "modified=5; untracked=1; staged=0; runtime_artifacts=0; "
        "benchmark_results=0; dirty_benchmark_results=0; release_evidence=0; "
        "generated_policy=true; "
        "branch=codex/qa-z-bootstrap; "
        "head=1234567890abcdef1234567890abcdef12345678; "
        "areas=source:3, tests:2, docs:1" in guide
    )
    assert "Safety Package" in guide
    assert "Return Contract" in guide
    assert "result_template.json" in guide
    assert "python -m qa_z repair-session verify" in guide
    assert "QA-Z Executor Bridge for Codex" in codex
    assert "Bridge id: `bridge-one`" in codex
    assert "Live repository:" in codex
    assert "executor_safety.md" in codex
    assert "QA-Z Executor Bridge for Claude" in claude
    assert "Do not call Codex or Claude APIs from QA-Z" in claude
    assert "Live repository:" in claude
    assert "executor_safety.md" in claude
    assert f"Safety rule count: `{expected_rule_count}`" in guide
    assert f"Safety rule count: `{expected_rule_count}`" in codex
    assert f"Safety rule count: `{expected_rule_count}`" in claude
    placeholder_guidance = (
        f"Replace the placeholder summary before ingest: `{PLACEHOLDER_SUMMARY}`"
    )
    assert placeholder_guidance in guide
    assert placeholder_guidance in codex
    assert placeholder_guidance in claude
    assert safety_json["kind"] == "qa_z.executor_safety"
    assert safety_markdown.startswith("# QA-Z Pre-Live Executor Safety Package")


def test_executor_bridge_from_older_loop_keeps_loop_local_self_inspection(
    tmp_path: Path,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_fast_summary(tmp_path, "candidate", status="passed", exit_code=0)
    write_regressed_verify_artifacts(tmp_path)

    first = run_autonomy(
        root=tmp_path,
        config=load_config(tmp_path),
        loops=1,
        count=1,
        now="2026-04-15T00:00:00Z",
    )
    first_loop_id = first["latest_loop_id"]
    run_autonomy(
        root=tmp_path,
        config=load_config(tmp_path),
        loops=1,
        count=1,
        now="2026-04-15T00:01:00Z",
    )

    result = create_executor_bridge(
        root=tmp_path,
        from_loop=first_loop_id,
        bridge_id="bridge-old-loop",
        now=NOW,
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    copied_outcome = json.loads(
        (
            tmp_path
            / ".qa-z"
            / "executor"
            / "bridge-old-loop"
            / "inputs"
            / "autonomy_outcome.json"
        ).read_text(encoding="utf-8")
    )

    assert manifest["source_loop_id"] == first_loop_id
    assert manifest["source_self_inspection"] == (
        f".qa-z/loops/{first_loop_id}/self_inspect.json"
    )
    assert manifest["source_self_inspection"] != ".qa-z/loops/latest/self_inspect.json"
    assert (
        copied_outcome["source_self_inspection"] == manifest["source_self_inspection"]
    )


def test_executor_bridge_from_session_without_loop_uses_session_inputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
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
        ]
    )
    capsys.readouterr()

    result = create_executor_bridge(
        root=tmp_path,
        from_session=".qa-z/sessions/session-one",
        bridge_id="bridge-session",
        now=NOW,
    )

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))

    assert start_exit == 0
    assert manifest["source_loop_id"] is None
    assert manifest["source_session_id"] == "session-one"
    assert "source_self_inspection" not in manifest
    assert "live_repository" not in manifest
    assert manifest["selected_task_ids"] == []
    assert manifest["prepared_action_type"] == "repair_session"
    assert manifest["inputs"]["autonomy_outcome"] is None
    assert manifest["safety_package"]["policy_json"].endswith("executor_safety.json")
    assert (tmp_path / ".qa-z" / "executor" / "bridge-session" / "codex.md").exists()
    assert (tmp_path / ".qa-z" / "executor" / "bridge-session" / "claude.md").exists()


def test_executor_bridge_copies_repair_action_context_inputs(
    tmp_path: Path,
) -> None:
    loop_id, _session_id = prepare_autonomy_session(tmp_path)

    result = create_executor_bridge(
        root=tmp_path,
        from_loop=loop_id,
        bridge_id="bridge-context",
        now=NOW,
    )

    bridge_dir = tmp_path / ".qa-z" / "executor" / "bridge-context"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    guide = (bridge_dir / "executor_guide.md").read_text(encoding="utf-8")
    codex = (bridge_dir / "codex.md").read_text(encoding="utf-8")
    copied_self_inspection = bridge_dir / "inputs" / "context" / "001-self_inspect.json"
    copied_summary = bridge_dir / "inputs" / "context" / "002-summary.json"

    assert manifest["inputs"]["action_context"] == [
        {
            "source_path": ".qa-z/loops/loop-20260415-000000-01/self_inspect.json",
            "copied_path": (
                ".qa-z/executor/bridge-context/inputs/context/001-self_inspect.json"
            ),
        },
        {
            "source_path": ".qa-z/runs/candidate/verify/summary.json",
            "copied_path": (
                ".qa-z/executor/bridge-context/inputs/context/002-summary.json"
            ),
        },
    ]
    assert manifest["inputs"]["action_context_missing"] == []
    assert copied_self_inspection.exists()
    assert copied_summary.exists()
    assert json.loads(copied_self_inspection.read_text(encoding="utf-8"))[
        "loop_id"
    ] == (loop_id)
    assert json.loads(copied_summary.read_text(encoding="utf-8"))["verdict"] == (
        "regressed"
    )
    assert "Action context" in guide
    assert ".qa-z/executor/bridge-context/inputs/context/001-self_inspect.json" in guide
    assert ".qa-z/executor/bridge-context/inputs/context/002-summary.json" in guide
    assert ".qa-z/executor/bridge-context/inputs/context/001-self_inspect.json" in codex
    assert ".qa-z/executor/bridge-context/inputs/context/002-summary.json" in codex


def test_executor_bridge_rejects_required_inputs_outside_repository(
    tmp_path: Path,
) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    outside.write_text("do not package me\n", encoding="utf-8")

    with pytest.raises(ArtifactSourceNotFound, match="outside repository root"):
        copy_input(
            root=tmp_path,
            source=outside,
            target=tmp_path / ".qa-z" / "executor" / "bridge" / "inputs" / "x.txt",
        )

    assert not (
        tmp_path / ".qa-z" / "executor" / "bridge" / "inputs" / "x.txt"
    ).exists()


def test_executor_bridge_guides_show_missing_action_context_inputs(
    tmp_path: Path,
) -> None:
    loop_id, _session_id = prepare_autonomy_session(tmp_path)
    outcome_path = tmp_path / ".qa-z" / "loops" / loop_id / "outcome.json"
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    action = outcome["actions_prepared"][0]
    action["context_paths"] = [
        ".qa-z/runs/candidate/verify/summary.json",
        ".qa-z/runs/candidate/verify/missing-context.json",
    ]
    write_json(outcome_path, outcome)

    result = create_executor_bridge(
        root=tmp_path,
        from_loop=loop_id,
        bridge_id="bridge-missing-context",
        now=NOW,
    )

    bridge_dir = tmp_path / ".qa-z" / "executor" / "bridge-missing-context"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    guide = (bridge_dir / "executor_guide.md").read_text(encoding="utf-8")
    codex = (bridge_dir / "codex.md").read_text(encoding="utf-8")
    claude = (bridge_dir / "claude.md").read_text(encoding="utf-8")

    assert manifest["inputs"]["action_context_missing"] == [
        ".qa-z/runs/candidate/verify/missing-context.json"
    ]
    for text in (guide, codex, claude):
        assert "Action context missing" in text
        assert ".qa-z/runs/candidate/verify/missing-context.json" in text


def test_executor_bridge_backfills_missing_session_safety_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    start_exit = main(
        [
            "repair-session",
            "start",
            "--path",
            str(tmp_path),
            "--baseline-run",
            ".qa-z/runs/baseline",
            "--session-id",
            "session-backfill",
        ]
    )
    capsys.readouterr()

    session_dir = tmp_path / ".qa-z" / "sessions" / "session-backfill"
    manifest_path = session_dir / "session.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest.pop("safety_artifacts", None)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (session_dir / "executor_safety.json").unlink()
    (session_dir / "executor_safety.md").unlink()

    result = create_executor_bridge(
        root=tmp_path,
        from_session=".qa-z/sessions/session-backfill",
        bridge_id="bridge-backfill",
        now=NOW,
    )

    repaired_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert start_exit == 0
    assert repaired_manifest["safety_artifacts"]["policy_json"].endswith(
        "executor_safety.json"
    )
    assert repaired_manifest["safety_artifacts"]["policy_markdown"].endswith(
        "executor_safety.md"
    )
    assert (session_dir / "executor_safety.json").exists()
    assert (session_dir / "executor_safety.md").exists()
    assert (
        tmp_path
        / ".qa-z"
        / "executor"
        / "bridge-backfill"
        / "inputs"
        / "executor_safety.json"
    ).exists()
    assert result.manifest_path.exists()


def test_executor_bridge_requires_repair_session_action_for_loop(
    tmp_path: Path,
) -> None:
    loop_dir = tmp_path / ".qa-z" / "loops" / "loop-no-session"
    write_json(
        loop_dir / "outcome.json",
        {
            "kind": "qa_z.autonomy_outcome",
            "schema_version": 1,
            "loop_id": "loop-no-session",
            "selected_task_ids": ["docs_drift-self_improvement_commands"],
            "actions_prepared": [
                {
                    "type": "docs_sync_plan",
                    "task_id": "docs_drift-self_improvement_commands",
                }
            ],
        },
    )

    with pytest.raises(ExecutorBridgeError, match="repair_session action"):
        create_executor_bridge(root=tmp_path, from_loop="loop-no-session")


def test_executor_bridge_cli_from_loop_and_missing_session(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loop_id, _session_id = prepare_autonomy_session(tmp_path)

    exit_code = main(
        [
            "executor-bridge",
            "--path",
            str(tmp_path),
            "--from-loop",
            loop_id,
            "--bridge-id",
            "bridge-cli",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    missing_exit = main(
        [
            "executor-bridge",
            "--path",
            str(tmp_path),
            "--from-session",
            ".qa-z/sessions/missing",
        ]
    )
    missing_output = capsys.readouterr().out

    assert exit_code == 0
    assert output["kind"] == "qa_z.executor_bridge"
    assert output["bridge_id"] == "bridge-cli"
    assert (
        tmp_path / ".qa-z" / "executor" / "bridge-cli" / "executor_guide.md"
    ).exists()
    assert missing_exit == 4
    assert "qa-z executor-bridge: source not found:" in missing_output


def test_executor_bridge_cli_stdout_points_to_return_and_safety_entrypoints(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loop_id, session_id = prepare_autonomy_session(tmp_path)

    exit_code = main(
        [
            "executor-bridge",
            "--path",
            str(tmp_path),
            "--from-loop",
            loop_id,
            "--bridge-id",
            "bridge-stdout",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "qa-z executor-bridge: ready_for_external_executor" in output
    assert "Executor guide: .qa-z/executor/bridge-stdout/executor_guide.md" in output
    assert (
        "Result template: .qa-z/executor/bridge-stdout/result_template.json" in output
    )
    assert "Expected result: .qa-z/executor/bridge-stdout/result.json" in output
    assert (
        "Safety package: .qa-z/executor/bridge-stdout/inputs/executor_safety.md"
        in output
    )
    assert f"Safety rule count: {len(EXECUTOR_SAFETY_RULE_IDS)}" in output
    assert (
        "Live repository: modified=5; untracked=1; staged=0; "
        "runtime_artifacts=0; benchmark_results=0; dirty_benchmark_results=0; "
        "release_evidence=0; "
        "generated_policy=true; branch=codex/qa-z-bootstrap; "
        "head=1234567890abcdef1234567890abcdef12345678; "
        "areas=source:3, tests:2, docs:1" in output
    )
    assert (
        "Verify command: python -m qa_z repair-session verify --session "
        f".qa-z/sessions/{session_id} --rerun"
    ) in output
    assert "Template summary: replace placeholder before ingest" in output


def test_executor_bridge_cli_warns_for_output_dir_outside_qa_z(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loop_id, _session_id = prepare_autonomy_session(tmp_path)
    bridge_dir = tmp_path / "external-bridge-package"

    exit_code = main(
        [
            "executor-bridge",
            "--path",
            str(tmp_path),
            "--from-loop",
            loop_id,
            "--bridge-id",
            "bridge-outside",
            "--output-dir",
            str(bridge_dir),
        ]
    )
    output = capsys.readouterr().out
    manifest = json.loads((bridge_dir / "bridge.json").read_text(encoding="utf-8"))
    guide = (bridge_dir / "executor_guide.md").read_text(encoding="utf-8")
    codex = (bridge_dir / "codex.md").read_text(encoding="utf-8")
    claude = (bridge_dir / "claude.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert manifest["output_policy"] == {
        "under_repository_root": True,
        "under_qa_z": False,
        "under_default_executor_tree": False,
        "cleanup_managed_by_qaz": False,
        "contains_copied_evidence": True,
    }
    assert manifest["warnings"] == [
        {
            "id": "custom_output_dir_outside_qa_z",
            "message": (
                "Executor bridge package is outside .qa-z; keep this generated "
                "executor evidence local or intentionally manage it outside QA-Z "
                "cleanup and ignore policy."
            ),
        }
    ]
    assert "Warning: custom_output_dir_outside_qa_z" in output
    assert "outside .qa-z" in output
    assert "## Warnings" in guide
    assert "custom_output_dir_outside_qa_z" in guide
    assert "custom_output_dir_outside_qa_z" in codex
    assert "custom_output_dir_outside_qa_z" in claude


def test_executor_bridge_cli_warns_for_output_dir_outside_repository(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loop_id, _session_id = prepare_autonomy_session(tmp_path)
    bridge_dir = tmp_path.parent / f"{tmp_path.name}-outside-repo-bridge-package"

    exit_code = main(
        [
            "executor-bridge",
            "--path",
            str(tmp_path),
            "--from-loop",
            loop_id,
            "--bridge-id",
            "bridge-outside-repository",
            "--output-dir",
            str(bridge_dir),
        ]
    )
    output = capsys.readouterr().out
    manifest = json.loads((bridge_dir / "bridge.json").read_text(encoding="utf-8"))
    guide = (bridge_dir / "executor_guide.md").read_text(encoding="utf-8")
    codex = (bridge_dir / "codex.md").read_text(encoding="utf-8")
    claude = (bridge_dir / "claude.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert manifest["output_policy"] == {
        "under_repository_root": False,
        "under_qa_z": False,
        "under_default_executor_tree": False,
        "cleanup_managed_by_qaz": False,
        "contains_copied_evidence": True,
    }
    assert [warning["id"] for warning in manifest["warnings"]] == [
        "custom_output_dir_outside_repository",
        "custom_output_dir_outside_qa_z",
    ]
    assert "Warning: custom_output_dir_outside_repository" in output
    assert "Warning: custom_output_dir_outside_qa_z" in output
    assert "outside the repository root" in output
    assert "## Warnings" in guide
    for text in (guide, codex, claude):
        assert "custom_output_dir_outside_repository" in text
        assert "custom_output_dir_outside_qa_z" in text


def test_executor_bridge_removes_incomplete_custom_package_on_copy_failure(
    tmp_path: Path,
) -> None:
    loop_id, session_id = prepare_autonomy_session(tmp_path)
    session_dir = tmp_path / ".qa-z" / "sessions" / session_id
    (session_dir / "handoff" / "handoff.json").unlink()
    bridge_dir = tmp_path.parent / f"{tmp_path.name}-incomplete-bridge-package"

    with pytest.raises(ArtifactSourceNotFound, match="Required bridge input not found"):
        create_executor_bridge(
            root=tmp_path,
            from_loop=loop_id,
            bridge_id="bridge-incomplete",
            output_dir=bridge_dir,
            now=NOW,
        )

    assert not bridge_dir.exists()


def test_executor_bridge_cli_stdout_surfaces_missing_action_context(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loop_id, _session_id = prepare_autonomy_session(tmp_path)
    outcome_path = tmp_path / ".qa-z" / "loops" / loop_id / "outcome.json"
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    action = outcome["actions_prepared"][0]
    action["context_paths"] = [
        ".qa-z/runs/candidate/verify/summary.json",
        ".qa-z/runs/candidate/verify/missing-context.json",
    ]
    write_json(outcome_path, outcome)
    capsys.readouterr()

    exit_code = main(
        [
            "executor-bridge",
            "--path",
            str(tmp_path),
            "--from-loop",
            loop_id,
            "--bridge-id",
            "bridge-stdout-missing-context",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Action context inputs: 1" in output
    assert "Missing action context: 1" in output
    assert ".qa-z/runs/candidate/verify/missing-context.json" in output
