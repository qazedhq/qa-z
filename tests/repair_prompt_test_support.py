"""Shared fixture writers for repair-prompt and review-packet tests."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml


def write_config(tmp_path: Path) -> None:
    """Write a minimal qa-z config for artifact tests."""
    config = {
        "project": {"name": "qa-z-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {"output_dir": ".qa-z/runs"},
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(
    tmp_path: Path,
    *,
    name: str = "auth.md",
    title: str = "Markdown title",
    front_matter: bool = True,
) -> str:
    """Write a contract and return its repo-relative path."""
    contract_dir = tmp_path / "qa" / "contracts"
    contract_dir.mkdir(parents=True, exist_ok=True)
    if front_matter:
        body = dedent(
            f"""
            ---
            qa_z_contract_version: 1
            title: {title}
            summary: Refresh token handling must remain deterministic.
            scope:
              - token refresh path
              - expired token handling
            acceptance_checks:
              - invalid token returns 401
              - refresh flow preserves current CLI flags
            assumptions:
              - Existing token storage stays compatible
            constraints:
              - Do not weaken tests
              - Preserve existing CLI flags
            ---
            # QA Contract: Ignored markdown title

            ## Contract Summary

            Markdown fallback summary.

            ## Scope

            - fallback scope

            ## Acceptance Checks

            - fallback check

            ## Related Files

            - src/qa_z/runners/fast.py
            """
        ).strip()
    else:
        body = dedent(
            f"""
            # QA Contract: {title}

            ## Contract Summary

            Markdown fallback summary.

            ## Scope

            - token refresh path
            - expired token handling

            ## Assumptions

            - Existing token storage stays compatible

            ## Acceptance Checks

            - invalid token returns 401
            - refresh flow preserves current CLI flags

            ## Constraints

            - Do not weaken tests

            ## Changed Files

            - src/qa_z/runners/fast.py
            """
        ).strip()
    path = contract_dir / name
    path.write_text(body + "\n", encoding="utf-8")
    return f"qa/contracts/{name}"


def write_summary(
    tmp_path: Path,
    run_id: str,
    *,
    status: str = "failed",
    contract_path: str | None = "qa/contracts/auth.md",
    checks: list[dict[str, Any]] | None = None,
    selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Write a fast summary artifact and return its JSON payload."""
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
            },
        ]
    summary: dict[str, Any] = {
        "mode": "fast",
        "contract_path": contract_path,
        "project_root": str(tmp_path),
        "status": status,
        "started_at": "2026-04-11T17:38:52Z",
        "finished_at": "2026-04-11T17:39:11Z",
        "artifact_dir": f".qa-z/runs/{run_id}/fast",
        "checks": checks,
        "totals": {
            "passed": sum(1 for check in checks if check["status"] == "passed"),
            "failed": sum(1 for check in checks if check["status"] == "failed"),
            "skipped": sum(1 for check in checks if check["status"] == "skipped"),
            "warning": sum(1 for check in checks if check["status"] == "warning"),
        },
    }
    if selection is not None:
        summary["schema_version"] = 2
        summary["selection"] = selection
    summary_path = tmp_path / ".qa-z" / "runs" / run_id / "fast" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    return summary


def write_deep_summary(tmp_path: Path, run_id: str) -> dict[str, Any]:
    """Write a deep summary with Semgrep findings next to a fast run."""
    payload: dict[str, Any] = {
        "schema_version": 2,
        "mode": "deep",
        "contract_path": "qa/contracts/auth.md",
        "project_root": str(tmp_path),
        "status": "failed",
        "started_at": "2026-04-11T17:40:00Z",
        "finished_at": "2026-04-11T17:40:05Z",
        "artifact_dir": f".qa-z/runs/{run_id}/deep",
        "selection": {
            "mode": "smart",
            "input_source": "cli_diff",
            "changed_files": [
                {
                    "path": "src/app.py",
                    "old_path": "src/app.py",
                    "status": "modified",
                    "additions": 2,
                    "deletions": 1,
                    "language": "python",
                    "kind": "source",
                },
                {
                    "path": "src/db.ts",
                    "old_path": "src/db.ts",
                    "status": "modified",
                    "additions": 3,
                    "deletions": 1,
                    "language": "typescript",
                    "kind": "source",
                },
            ],
            "high_risk_reasons": [],
            "selected_checks": ["sg_scan"],
            "full_checks": [],
            "targeted_checks": ["sg_scan"],
            "skipped_checks": [],
        },
        "checks": [
            {
                "id": "sg_scan",
                "tool": "semgrep",
                "command": [
                    "semgrep",
                    "--config",
                    "auto",
                    "--json",
                    "src/app.py",
                    "src/db.ts",
                ],
                "kind": "static-analysis",
                "status": "failed",
                "exit_code": 0,
                "duration_ms": 321,
                "stdout_tail": "",
                "stderr_tail": "",
                "execution_mode": "targeted",
                "target_paths": ["src/app.py", "src/db.ts"],
                "selection_reason": "source files changed",
                "high_risk_reasons": [],
                "findings_count": 2,
                "severity_summary": {"ERROR": 1, "WARNING": 1},
                "findings": [
                    {
                        "rule_id": "python.lang.security.audit.eval",
                        "severity": "ERROR",
                        "path": "src/app.py",
                        "line": 42,
                        "message": "Avoid use of eval",
                    },
                    {
                        "rule_id": "typescript.sql.injection",
                        "severity": "WARNING",
                        "path": "src/db.ts",
                        "line": 12,
                        "message": "Possible SQL injection",
                    },
                ],
            }
        ],
        "totals": {"passed": 0, "failed": 1, "skipped": 0, "warning": 0},
    }
    summary_path = tmp_path / ".qa-z" / "runs" / run_id / "deep" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def write_grouped_deep_summary(tmp_path: Path, run_id: str) -> dict[str, Any]:
    """Write a deep summary with grouped Semgrep findings."""
    payload: dict[str, Any] = {
        "schema_version": 2,
        "mode": "deep",
        "contract_path": "qa/contracts/auth.md",
        "project_root": str(tmp_path),
        "status": "failed",
        "started_at": "2026-04-11T17:40:00Z",
        "finished_at": "2026-04-11T17:40:05Z",
        "artifact_dir": f".qa-z/runs/{run_id}/deep",
        "policy": {
            "config": "auto",
            "fail_on_severity": ["ERROR"],
            "ignore_rules": [],
            "exclude_paths": [],
        },
        "selection": {
            "mode": "smart",
            "input_source": "cli_diff",
            "changed_files": [],
            "high_risk_reasons": [],
            "selected_checks": ["sg_scan"],
            "full_checks": [],
            "targeted_checks": ["sg_scan"],
            "skipped_checks": [],
        },
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
                "execution_mode": "targeted",
                "target_paths": ["src/app.py", "src/db.ts"],
                "selection_reason": "source files changed",
                "high_risk_reasons": [],
                "findings_count": 5,
                "blocking_findings_count": 3,
                "filtered_findings_count": 0,
                "filter_reasons": {},
                "severity_summary": {"ERROR": 3, "WARNING": 2},
                "policy": {
                    "config": "auto",
                    "fail_on_severity": ["ERROR"],
                    "ignore_rules": [],
                    "exclude_paths": [],
                },
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
                "findings": [
                    {
                        "rule_id": "python.lang.security.audit.eval",
                        "severity": "ERROR",
                        "path": "src/app.py",
                        "line": 42,
                        "message": "Avoid use of eval",
                    },
                    {
                        "rule_id": "typescript.sql.injection",
                        "severity": "WARNING",
                        "path": "src/db.ts",
                        "line": 12,
                        "message": "Possible SQL injection",
                    },
                ],
            }
        ],
        "totals": {"passed": 0, "failed": 1, "skipped": 0, "warning": 0},
    }
    summary_path = tmp_path / ".qa-z" / "runs" / run_id / "deep" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def assert_repair_artifacts(tmp_path: Path, run_id: str) -> dict[str, Any]:
    """Load repair artifacts and assert both files exist."""
    repair_dir = tmp_path / ".qa-z" / "runs" / run_id / "repair"
    packet_path = repair_dir / "packet.json"
    prompt_path = repair_dir / "prompt.md"
    assert packet_path.exists()
    assert prompt_path.exists()
    prompt = prompt_path.read_text(encoding="utf-8")
    assert "# QA-Z Repair Prompt" in prompt
    return json.loads(packet_path.read_text(encoding="utf-8"))
