"""Behavior tests for run-aware review-packet surfaces."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main
from tests.repair_prompt_test_support import (
    write_config,
    write_contract,
    write_deep_summary,
    write_grouped_deep_summary,
    write_summary,
)


def test_review_from_run_includes_failed_checks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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


def test_review_packet_includes_deep_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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


def test_review_packet_uses_grouped_findings_for_deep_section(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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


def test_review_packet_handles_fast_only_run_without_deep(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
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
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, front_matter=False)

    exit_code = main(["review", "--path", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# QA-Z Review Packet" in output
    assert "## Reviewer Focus" in output
    assert "## Run Verdict" not in output


def test_review_then_repair_prompt_run_sequentially_in_same_process(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Sequential smoke contract")
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    review_exit = main(["review", "--path", str(tmp_path), "--from-run", "latest"])
    review_output = capsys.readouterr().out
    repair_exit = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    repair_packet = json.loads(capsys.readouterr().out)

    assert review_exit == 0
    assert "# QA-Z Review Packet" in review_output
    assert repair_exit == 0
    assert repair_packet["repair_needed"] is True
    assert repair_packet["contract"]["title"] == "Sequential smoke contract"
