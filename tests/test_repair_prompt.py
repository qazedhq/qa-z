"""Behavior tests for repair-prompt runtime surfaces."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from qa_z.cli import main
from tests.repair_prompt_test_support import (
    assert_repair_artifacts,
    write_config,
    write_contract,
    write_deep_summary,
    write_grouped_deep_summary,
    write_summary,
)


def test_repair_prompt_from_latest_failed_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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


@pytest.mark.parametrize(
    "from_run",
    [
        lambda tmp_path: str(tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z"),
        lambda tmp_path: str(
            tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z" / "fast"
        ),
        lambda tmp_path: str(
            tmp_path
            / ".qa-z"
            / "runs"
            / "2026-04-11T17-38-52Z"
            / "fast"
            / "summary.json"
        ),
    ],
)
def test_repair_prompt_accepts_run_path_variants(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    from_run,
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
            from_run(tmp_path),
            "--json",
        ]
    )
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["run"]["dir"] == ".qa-z/runs/2026-04-11T17-38-52Z"


def test_repair_prompt_contract_override(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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


def test_repair_prompt_cli_failures_report_expected_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    missing_exit = main(
        ["repair-prompt", "--path", str(tmp_path), "--from-run", "latest"]
    )
    missing_output = capsys.readouterr().out

    summary_path = tmp_path / ".qa-z" / "runs" / "bad" / "fast" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text("{not-json", encoding="utf-8")
    broken_exit = main(
        ["repair-prompt", "--path", str(tmp_path), "--from-run", "latest"]
    )
    broken_output = capsys.readouterr().out

    assert missing_exit == 4
    assert "source not found" in missing_output
    assert broken_exit == 2
    assert "artifact error" in broken_output


def test_repair_prompt_json_includes_selection_context(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
