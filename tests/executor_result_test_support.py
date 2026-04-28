"""Shared support helpers for executor-result dry-run tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml

from qa_z.cli import main
from qa_z.executor_bridge import create_executor_bridge

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


def write_executor_result(path: Path, payload: dict[str, Any]) -> None:
    """Write an executor result fixture."""
    write_json(path, payload)


def read_json(path: Path) -> dict[str, Any]:
    """Read a deterministic JSON object fixture."""
    return json.loads(path.read_text(encoding="utf-8"))


def start_session_and_bridge(
    tmp_path: Path,
    capsys,
    *,
    session_id: str = "session-one",
    bridge_id: str = "bridge-session",
) -> tuple[Path, Any]:
    """Create a repair session and executor bridge for dry-run tests."""
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
