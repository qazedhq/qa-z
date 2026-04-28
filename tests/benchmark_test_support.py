from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent


def write_expected(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_config(
    root: Path,
    checks: list[dict[str, object]],
    *,
    languages: list[str] | None = None,
) -> None:
    config = {
        "project": {
            "name": "benchmark-fixture",
            "languages": languages or ["python"],
        },
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "fail_on_missing_tool": True,
            "checks": checks,
        },
        "deep": {"checks": []},
    }
    root.joinpath("qa-z.yaml").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )


def write_contract(
    root: Path,
    *,
    related_files: list[str] | None = None,
    title: str = "Benchmark fixture",
) -> None:
    contract = root / "qa" / "contracts" / "contract.md"
    contract.parent.mkdir(parents=True, exist_ok=True)
    files = related_files or ["src/app.py"]
    contract.write_text(
        dedent(
            f"""
            # QA Contract: {title}

            ## Related Files

            {chr(10).join(f"- {path}" for path in files)}

            ## Acceptance Checks

            - Configured fast checks must pass.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_fast_summary(
    root: Path, run_id: str, *, check_id: str, status: str, exit_code: int | None
) -> None:
    run_dir = root / ".qa-z" / "runs" / run_id / "fast"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "mode": "fast",
        "contract_path": "qa/contracts/contract.md",
        "project_root": str(root),
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
                "stdout_tail": "",
                "stderr_tail": "",
            }
        ],
    }
    run_dir.joinpath("summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_mixed_fast_summary(
    root: Path,
    run_id: str,
    *,
    py_status: str,
    py_exit_code: int | None,
    ts_status: str,
    ts_exit_code: int | None,
) -> None:
    run_dir = root / ".qa-z" / "runs" / run_id / "fast"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "mode": "fast",
        "contract_path": "qa/contracts/contract.md",
        "project_root": str(root),
        "status": "failed"
        if {py_status, ts_status} & {"failed", "error"}
        else "passed",
        "started_at": "2026-04-14T00:00:00Z",
        "finished_at": "2026-04-14T00:00:01Z",
        "artifact_dir": f".qa-z/runs/{run_id}/fast",
        "checks": [
            {
                "id": "py_test",
                "tool": "pytest",
                "command": ["pytest", "-q"],
                "kind": "test",
                "status": py_status,
                "exit_code": py_exit_code,
                "duration_ms": 1,
                "stdout_tail": "",
                "stderr_tail": "",
            },
            {
                "id": "ts_type",
                "tool": "tsc",
                "command": ["tsc", "--noEmit"],
                "kind": "typecheck",
                "status": ts_status,
                "exit_code": ts_exit_code,
                "duration_ms": 1,
                "stdout_tail": "",
                "stderr_tail": "",
            },
        ],
    }
    run_dir.joinpath("summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
