"""Tests for normalized repair handoff packets and adapter renderers."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest
import yaml

from qa_z.artifacts import RunSource, load_contract_context
from qa_z.cli import main
from qa_z.reporters.repair_prompt import build_repair_packet
from qa_z.repair_handoff import build_repair_handoff, repair_handoff_json
from qa_z.runners.models import RunSummary
from qa_z.adapters.claude import render_claude_handoff
from qa_z.adapters.codex import render_codex_handoff


def write_config(tmp_path: Path) -> None:
    """Write a minimal QA-Z config for handoff tests."""
    config = {
        "project": {"name": "qa-z-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {"output_dir": ".qa-z/runs"},
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(tmp_path: Path) -> str:
    """Write a contract and return its repository-relative path."""
    path = tmp_path / "qa" / "contracts" / "auth.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        dedent(
            """
            ---
            qa_z_contract_version: 1
            title: Auth token refresh flow
            summary: Refresh token handling must remain deterministic.
            scope:
              - token refresh path
            acceptance_checks:
              - invalid token returns 401
            constraints:
              - Preserve existing CLI flags
            ---
            # QA Contract: Auth token refresh flow

            ## Related Files

            - src/qa_z/runners/fast.py
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    return "qa/contracts/auth.md"


def write_fast_summary(
    tmp_path: Path,
    *,
    run_id: str = "2026-04-14T12-00-00Z",
    status: str = "failed",
    checks: list[dict[str, Any]] | None = None,
) -> RunSummary:
    """Write and return a fast run summary."""
    if checks is None:
        checks = [
            {
                "id": "py_type",
                "tool": "mypy",
                "command": ["mypy", "src", "tests"],
                "kind": "typecheck",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 941,
                "stdout_tail": "src/qa_z/runners/fast.py:10: error: bad return\n",
                "stderr_tail": "",
            },
            {
                "id": "py_format",
                "tool": "ruff",
                "command": ["ruff", "format", "--check", "."],
                "kind": "format",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 113,
                "stdout_tail": "Would reformat tests/test_cli.py\n",
                "stderr_tail": "",
            },
        ]
    payload: dict[str, Any] = {
        "schema_version": 2,
        "mode": "fast",
        "contract_path": "qa/contracts/auth.md",
        "project_root": str(tmp_path),
        "status": status,
        "started_at": "2026-04-14T12:00:00Z",
        "finished_at": "2026-04-14T12:01:00Z",
        "artifact_dir": f".qa-z/runs/{run_id}/fast",
        "selection": {
            "mode": "smart",
            "input_source": "cli_diff",
            "changed_files": [],
            "high_risk_reasons": [],
            "selected_checks": [check["id"] for check in checks],
            "full_checks": ["py_type"],
            "targeted_checks": ["py_format"],
            "skipped_checks": [],
        },
        "checks": checks,
        "totals": {
            "passed": sum(1 for check in checks if check["status"] == "passed"),
            "failed": sum(1 for check in checks if check["status"] == "failed"),
            "skipped": sum(1 for check in checks if check["status"] == "skipped"),
            "warning": sum(1 for check in checks if check["status"] == "warning"),
        },
    }
    summary_path = tmp_path / ".qa-z" / "runs" / run_id / "fast" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    return RunSummary.from_dict(payload)


def grouped_deep_summary(tmp_path: Path, *, run_id: str) -> RunSummary:
    """Return a deep summary with one blocking and one non-blocking group."""
    payload: dict[str, Any] = {
        "schema_version": 2,
        "mode": "deep",
        "contract_path": "qa/contracts/auth.md",
        "project_root": str(tmp_path),
        "status": "failed",
        "started_at": "2026-04-14T12:02:00Z",
        "finished_at": "2026-04-14T12:03:00Z",
        "artifact_dir": f".qa-z/runs/{run_id}/deep",
        "policy": {"fail_on_severity": ["ERROR"]},
        "checks": [
            {
                "id": "sg_scan",
                "tool": "semgrep",
                "command": ["semgrep", "--config", "auto", "--json"],
                "kind": "static-analysis",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 321,
                "stdout_tail": "",
                "stderr_tail": "",
                "findings_count": 5,
                "blocking_findings_count": 3,
                "filtered_findings_count": 0,
                "filter_reasons": {},
                "severity_summary": {"ERROR": 3, "WARNING": 2},
                "policy": {"fail_on_severity": ["ERROR"]},
                "grouped_findings": [
                    {
                        "rule_id": "python.lang.security.audit.eval",
                        "severity": "ERROR",
                        "path": "src/app.py",
                        "count": 3,
                        "representative_line": 42,
                        "message": "Avoid use of eval",
                    },
                    {
                        "rule_id": "typescript.sql.injection",
                        "severity": "WARNING",
                        "path": "src/db.ts",
                        "count": 2,
                        "representative_line": 12,
                        "message": "Possible SQL injection",
                    },
                ],
                "findings": [],
            }
        ],
        "totals": {"passed": 0, "failed": 1, "skipped": 0, "warning": 0},
    }
    summary_path = tmp_path / ".qa-z" / "runs" / run_id / "deep" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    return RunSummary.from_dict(payload)


def build_handoff(tmp_path: Path, *, deep: RunSummary | None = None):
    """Build a normalized handoff from local test artifacts."""
    run_id = "2026-04-14T12-00-00Z"
    write_config(tmp_path)
    write_contract(tmp_path)
    summary = write_fast_summary(tmp_path, run_id=run_id)
    contract = load_contract_context(
        tmp_path / "qa" / "contracts" / "auth.md", tmp_path
    )
    run_source = RunSource(
        run_dir=tmp_path / ".qa-z" / "runs" / run_id,
        fast_dir=tmp_path / ".qa-z" / "runs" / run_id / "fast",
        summary_path=tmp_path / ".qa-z" / "runs" / run_id / "fast" / "summary.json",
    )
    repair_packet = build_repair_packet(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=tmp_path,
        deep_summary=deep,
    )
    return build_repair_handoff(
        repair_packet=repair_packet,
        summary=summary,
        run_source=run_source,
        root=tmp_path,
        deep_summary=deep,
    )


def test_handoff_model_selects_failed_checks_and_blocking_grouped_findings(
    tmp_path: Path,
) -> None:
    deep = grouped_deep_summary(tmp_path, run_id="2026-04-14T12-00-00Z")
    handoff = build_handoff(tmp_path, deep=deep)
    data = handoff.to_dict()

    assert data["kind"] == "qa_z.repair_handoff"
    assert data["schema_version"] == 1
    assert data["repair"]["repair_needed"] is True
    assert [target["id"] for target in data["repair"]["targets"]] == [
        "check:py_format",
        "check:py_type",
        "deep:python.lang.security.audit.eval:src/app.py",
    ]
    assert data["repair"]["targets"][2]["occurrences"] == 3
    assert "src/db.ts" not in data["repair"]["affected_files"]
    assert data["repair"]["affected_files"] == [
        "src/qa_z/runners/fast.py",
        "tests/test_cli.py",
        "src/app.py",
    ]
    assert data["validation"]["commands"] == [
        {
            "id": "check:py_format",
            "command": ["ruff", "format", "--check", "."],
            "success_criteria": "Command exits with code 0.",
        },
        {
            "id": "check:py_type",
            "command": ["mypy", "src", "tests"],
            "success_criteria": "Command exits with code 0.",
        },
        {
            "id": "qa-z-fast",
            "command": ["python", "-m", "qa_z", "fast"],
            "success_criteria": "qa-z fast exits with code 0.",
        },
        {
            "id": "qa-z-deep",
            "command": ["python", "-m", "qa_z", "deep", "--from-run", "latest"],
            "success_criteria": "qa-z deep exits with code 0 and no blocking findings remain.",
        },
    ]


def test_handoff_model_handles_no_blocking_findings(tmp_path: Path) -> None:
    run_id = "2026-04-14T12-00-00Z"
    write_config(tmp_path)
    write_contract(tmp_path)
    summary = write_fast_summary(
        tmp_path,
        run_id=run_id,
        status="passed",
        checks=[
            {
                "id": "py_test",
                "tool": "pytest",
                "command": ["pytest", "-q"],
                "kind": "test",
                "status": "passed",
                "exit_code": 0,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        ],
    )
    contract = load_contract_context(
        tmp_path / "qa" / "contracts" / "auth.md", tmp_path
    )
    run_source = RunSource(
        run_dir=tmp_path / ".qa-z" / "runs" / run_id,
        fast_dir=tmp_path / ".qa-z" / "runs" / run_id / "fast",
        summary_path=tmp_path / ".qa-z" / "runs" / run_id / "fast" / "summary.json",
    )
    repair_packet = build_repair_packet(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=tmp_path,
    )

    handoff = build_repair_handoff(
        repair_packet=repair_packet,
        summary=summary,
        run_source=run_source,
        root=tmp_path,
    )

    assert handoff.repair_needed is False
    assert handoff.targets == []
    assert handoff.to_dict()["validation"]["commands"] == [
        {
            "id": "qa-z-fast",
            "command": ["python", "-m", "qa_z", "fast"],
            "success_criteria": "qa-z fast exits with code 0.",
        }
    ]


def test_adapter_renderers_use_same_handoff_data(tmp_path: Path) -> None:
    handoff = build_handoff(tmp_path)

    codex = render_codex_handoff(handoff)
    claude = render_claude_handoff(handoff)

    assert codex.startswith("# QA-Z Codex Repair Handoff\n")
    assert "Implement the repair now." in codex
    assert "## Validation Commands" in codex
    assert "`python -m qa_z fast`" in codex
    assert claude.startswith("# QA-Z Claude Repair Handoff\n")
    assert "Analyze the QA-Z evidence, then make the smallest safe repair." in claude
    assert "## Non-Goals" in claude
    assert "`python -m qa_z fast`" in claude


def test_handoff_json_is_stable_and_machine_readable(tmp_path: Path) -> None:
    handoff = build_handoff(tmp_path)

    data = json.loads(repair_handoff_json(handoff))

    assert list(data) == [
        "constraints",
        "generated_at",
        "kind",
        "project",
        "provenance",
        "repair",
        "schema_version",
        "validation",
        "workflow",
    ]
    assert data["repair"]["targets"][0]["id"] == "check:py_format"


def test_repair_prompt_cli_writes_handoff_and_adapter_artifacts(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_id = "2026-04-14T12-00-00Z"
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, run_id=run_id)

    exit_code = main(
        [
            "repair-prompt",
            "--path",
            str(tmp_path),
            "--from-run",
            "latest",
            "--adapter",
            "codex",
        ]
    )
    output = capsys.readouterr().out
    repair_dir = tmp_path / ".qa-z" / "runs" / run_id / "repair"

    assert exit_code == 0
    assert "# QA-Z Codex Repair Handoff" in output
    assert (repair_dir / "packet.json").exists()
    assert (repair_dir / "prompt.md").exists()
    assert (repair_dir / "handoff.json").exists()
    assert (repair_dir / "codex.md").exists()
    assert (repair_dir / "claude.md").exists()
    handoff = json.loads((repair_dir / "handoff.json").read_text(encoding="utf-8"))
    assert handoff["kind"] == "qa_z.repair_handoff"


def test_repair_prompt_cli_can_print_handoff_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path)

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--handoff-json"])
    handoff = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert handoff["kind"] == "qa_z.repair_handoff"
    assert handoff["repair"]["targets"][0]["id"] == "check:py_format"
