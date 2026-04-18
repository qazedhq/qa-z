"""Tests for run-aware repair and review packets."""

from __future__ import annotations

import json
import os
from textwrap import dedent
from typing import Any

import pytest
import yaml

from qa_z.cli import main
from qa_z.reporters.repair_prompt import extract_candidate_files


def write_config(tmp_path) -> None:
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
    tmp_path,
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
    tmp_path,
    run_id: str,
    *,
    status: str = "failed",
    contract_path: str | None = "qa/contracts/auth.md",
    checks: list[dict] | None = None,
    selection: dict | None = None,
) -> dict:
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


def write_deep_summary(tmp_path, run_id: str) -> dict:
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


def write_grouped_deep_summary(tmp_path, run_id: str) -> dict:
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


def assert_repair_artifacts(tmp_path, run_id: str) -> dict:
    """Load repair artifacts and assert both files exist."""
    repair_dir = tmp_path / ".qa-z" / "runs" / run_id / "repair"
    packet_path = repair_dir / "packet.json"
    prompt_path = repair_dir / "prompt.md"
    assert packet_path.exists()
    assert prompt_path.exists()
    prompt = prompt_path.read_text(encoding="utf-8")
    assert "# QA-Z Repair Prompt" in prompt
    return json.loads(packet_path.read_text(encoding="utf-8"))


def test_repair_prompt_from_latest_failed_run(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Auth token refresh flow")
    older = write_summary(tmp_path, "2026-04-11T17-38-52Z")
    newer = write_summary(tmp_path, "2026-04-11T18-38-52Z")
    os.utime(
        tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z" / "fast" / "summary.json",
        (1, 1),
    )
    os.utime(
        tmp_path / ".qa-z" / "runs" / "2026-04-11T18-38-52Z" / "fast" / "summary.json",
        (2, 2),
    )

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out
    packet = assert_repair_artifacts(tmp_path, "2026-04-11T18-38-52Z")

    assert exit_code == 0
    assert "# QA-Z Repair Prompt" in output
    assert packet["repair_needed"] is True
    assert packet["run"]["dir"] == ".qa-z/runs/2026-04-11T18-38-52Z"
    assert packet["run"]["status"] == newer["status"]
    assert packet["run"]["status"] != older["status"] or packet["run"]["dir"].endswith(
        "18-38-52Z"
    )
    assert packet["contract"]["title"] == "Auth token refresh flow"
    assert [failure["id"] for failure in packet["failures"]] == [
        "py_format",
        "py_type",
    ]
    assert packet["suggested_fix_order"] == ["py_format", "py_type"]
    assert "agent_prompt" in packet


def test_repair_prompt_from_run_root_path(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(
        [
            "repair-prompt",
            "--path",
            str(tmp_path),
            "--from-run",
            str(tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z"),
            "--json",
        ]
    )
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["run"]["dir"] == ".qa-z/runs/2026-04-11T17-38-52Z"


def test_repair_prompt_from_fast_dir_path(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(
        [
            "repair-prompt",
            "--path",
            str(tmp_path),
            "--from-run",
            str(tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z" / "fast"),
            "--json",
        ]
    )
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["run"]["dir"] == ".qa-z/runs/2026-04-11T17-38-52Z"


def test_repair_prompt_from_summary_json_path(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(
        [
            "repair-prompt",
            "--path",
            str(tmp_path),
            "--from-run",
            str(
                tmp_path
                / ".qa-z"
                / "runs"
                / "2026-04-11T17-38-52Z"
                / "fast"
                / "summary.json"
            ),
            "--json",
        ]
    )
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["run"]["dir"] == ".qa-z/runs/2026-04-11T17-38-52Z"


def test_repair_prompt_contract_override(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, name="summary.md", title="Summary contract")
    override_path = write_contract(
        tmp_path, name="override.md", title="Override contract"
    )
    write_summary(
        tmp_path,
        "2026-04-11T17-38-52Z",
        contract_path="qa/contracts/summary.md",
    )

    exit_code = main(
        [
            "repair-prompt",
            "--path",
            str(tmp_path),
            "--from-run",
            "latest",
            "--contract",
            str(tmp_path / override_path),
            "--json",
        ]
    )
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["contract"]["path"] == override_path
    assert packet["contract"]["title"] == "Override contract"


def test_repair_prompt_passing_run_sets_repair_needed_false(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(
        tmp_path,
        "2026-04-11T17-38-52Z",
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

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["repair_needed"] is False
    assert packet["failures"] == []
    assert packet["done_when"] == ["No repair required; source run already passed"]


def test_repair_prompt_missing_run_returns_4(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out

    assert exit_code == 4
    assert "source not found" in output


def test_repair_prompt_broken_summary_returns_2(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    summary_path = tmp_path / ".qa-z" / "runs" / "bad" / "fast" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("{not-json", encoding="utf-8")

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out

    assert exit_code == 2
    assert "artifact error" in output


def test_review_from_run_includes_failed_checks(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Auth token refresh flow")
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["review", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# QA-Z Review Packet" in output
    assert "## Run Verdict" in output
    assert "- Status: failed" in output
    assert "### py_type" in output
    assert "src/qa_z/runners/fast.py" in output
    assert "## Review Priority Order" in output


def test_review_includes_deep_findings(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Auth token refresh flow")
    write_summary(tmp_path, "2026-04-11T17-38-52Z", status="passed", checks=[])
    write_deep_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["review", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Deep Findings" in output
    assert "- Findings: 2" in output
    assert "- Highest severity: ERROR" in output
    assert "- Severity summary: ERROR: 1, WARNING: 1" in output
    assert "- Affected files: `src/app.py`, `src/db.ts`" in output
    assert "- `sg_scan` ran in targeted mode for 2 files" in output
    assert (
        "- `src/app.py:42` ERROR python.lang.security.audit.eval - Avoid use of eval"
        in output
    )


def test_review_uses_grouped_findings_for_deep_section(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Auth token refresh flow")
    write_summary(tmp_path, "2026-04-11T17-38-52Z", status="passed", checks=[])
    write_grouped_deep_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["review", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "- Blocking findings: 3" in output
    assert "- Filtered findings: 0" in output
    assert "Top grouped findings:" in output
    assert (
        "- `python.lang.security.audit.eval` in `src/app.py:42` "
        "(3 occurrences) - Avoid use of eval"
    ) in output


def test_review_handles_fast_only_run_without_deep(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Auth token refresh flow")
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["review", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Run Verdict" in output
    assert "## Deep Findings" not in output


def test_review_from_run_writes_output_dir(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Auth token refresh flow")
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    output_dir = tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z" / "review"

    exit_code = main(
        [
            "review",
            "--path",
            str(tmp_path),
            "--from-run",
            "latest",
            "--output-dir",
            str(output_dir),
        ]
    )
    capsys.readouterr()

    assert exit_code == 0
    assert "# QA-Z Review Packet" in (output_dir / "review.md").read_text(
        encoding="utf-8"
    )
    assert (
        json.loads((output_dir / "review.json").read_text(encoding="utf-8"))["run"][
            "status"
        ]
        == "failed"
    )


def test_review_from_run_includes_selection_context(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(
        tmp_path,
        "2026-04-11T17-38-52Z",
        status="passed",
        checks=[
            {
                "id": "py_lint",
                "tool": "ruff",
                "command": ["ruff", "check", "src/qa_z/cli.py"],
                "kind": "lint",
                "status": "passed",
                "exit_code": 0,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
                "execution_mode": "targeted",
                "target_paths": ["src/qa_z/cli.py"],
                "selection_reason": "python source/test files changed",
                "high_risk_reasons": [],
            }
        ],
        selection={
            "mode": "smart",
            "input_source": "cli_diff",
            "changed_files": [
                {
                    "path": "src/qa_z/cli.py",
                    "old_path": "src/qa_z/cli.py",
                    "status": "modified",
                    "additions": 1,
                    "deletions": 1,
                    "language": "python",
                    "kind": "source",
                }
            ],
            "high_risk_reasons": [],
            "selected_checks": ["py_lint"],
            "full_checks": [],
            "targeted_checks": ["py_lint"],
            "skipped_checks": [],
        },
    )

    exit_code = main(["review", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "## Check Selection" in output
    assert "- Mode: smart" in output
    assert "- Targeted checks: py_lint" in output


def test_review_without_run_keeps_existing_behavior(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, front_matter=False)

    exit_code = main(["review", "--path", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# QA-Z Review Packet" in output
    assert "## Reviewer Focus" in output
    assert "## Run Verdict" not in output


def test_repair_prompt_json_includes_selection_context(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(
        tmp_path,
        "2026-04-11T17-38-52Z",
        status="passed",
        checks=[],
        selection={
            "mode": "smart",
            "input_source": "contract",
            "changed_files": [],
            "high_risk_reasons": ["no change information available"],
            "selected_checks": [],
            "full_checks": [],
            "targeted_checks": [],
            "skipped_checks": [],
        },
    )

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["run"]["selection"]["mode"] == "smart"
    assert (
        "no change information available"
        in packet["run"]["selection"]["high_risk_reasons"]
    )


def test_repair_prompt_includes_deep_findings(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z", status="passed", checks=[])
    write_deep_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["repair_needed"] is True
    assert packet["deep"]["findings_count"] == 2
    assert packet["deep"]["highest_severity"] == "ERROR"
    assert "## Security Findings (Semgrep)" in packet["agent_prompt"]
    assert (
        "`src/app.py:42` ERROR python.lang.security.audit.eval - Avoid use of eval"
        in packet["agent_prompt"]
    )
    assert (
        "`src/db.ts:12` WARNING typescript.sql.injection - Possible SQL injection"
        in packet["agent_prompt"]
    )


def test_repair_prompt_uses_grouped_blocking_findings(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z", status="passed", checks=[])
    write_grouped_deep_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["repair_needed"] is True
    assert packet["deep"]["blocking_findings_count"] == 3
    assert "## Deep QA Findings" in packet["agent_prompt"]
    assert (
        "- `python.lang.security.audit.eval` in `src/app.py:42` "
        "(3 occurrences) - Avoid use of eval"
    ) in packet["agent_prompt"]
    assert "typescript.sql.injection" not in packet["agent_prompt"]


def test_candidate_files_extracted_from_failure_output() -> None:
    text = dedent(
        """
        tests/test_cli.py:10: assertion failed
        src\\qa_z\\runners\\fast.py:20: error
        ignored.txt
        app/components/Login.tsx(12,2): error
        """
    )

    assert extract_candidate_files(text) == [
        "tests/test_cli.py",
        "src/qa_z/runners/fast.py",
        "app/components/Login.tsx",
    ]


def test_contract_front_matter_preferred_over_markdown_scrape(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Front matter title")
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["contract"]["title"] == "Front matter title"
    assert packet["contract"]["scope_items"] == [
        "token refresh path",
        "expired token handling",
    ]
    assert "fallback scope" not in packet["contract"]["scope_items"]


def test_markdown_fallback_when_front_matter_missing(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Markdown fallback title", front_matter=False)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["contract"]["title"] == "Markdown fallback title"
    assert packet["contract"]["summary"] == "Markdown fallback summary."


def test_suggested_fix_order_is_stable(
    tmp_path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(
        tmp_path,
        "2026-04-11T17-38-52Z",
        checks=[
            {
                "id": "py_test",
                "tool": "pytest",
                "command": ["pytest", "-q"],
                "kind": "test",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
            },
            {
                "id": "py_type",
                "tool": "mypy",
                "command": ["mypy", "src", "tests"],
                "kind": "typecheck",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
            },
            {
                "id": "py_lint",
                "tool": "ruff",
                "command": ["ruff", "check", "."],
                "kind": "lint",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
            },
            {
                "id": "py_format",
                "tool": "ruff",
                "command": ["ruff", "format", "--check", "."],
                "kind": "format",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
            },
        ],
    )

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["suggested_fix_order"] == [
        "py_format",
        "py_lint",
        "py_type",
        "py_test",
    ]
