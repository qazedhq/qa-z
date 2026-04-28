"""Behavior tests for GitHub summary deep-context rendering."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_z.cli import main
from tests.github_summary_test_support import (
    write_config,
    write_contract,
    write_deep_summary,
    write_grouped_deep_summary,
    write_summary,
)


def test_github_summary_includes_deep_section(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    write_deep_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(
        ["github-summary", "--path", str(tmp_path), "--from-run", "latest"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "**Fast:** failed" in output
    assert "**Deep:** failed" in output
    assert "## Deep QA" in output
    assert "- Status: failed" in output
    assert "- Findings: 2" in output
    assert "- Highest severity: ERROR" in output
    assert "- Mode: targeted" in output
    assert "- Files affected: 2" in output
    assert "- `src/app.py:42` ERROR - Avoid use of eval" in output


def test_github_summary_uses_grouped_deep_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    write_grouped_deep_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(
        ["github-summary", "--path", str(tmp_path), "--from-run", "latest"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "- Blocking: 3" in output
    assert "### Top Deep Findings" in output
    assert "- `python.lang.security.audit.eval` - `src/app.py` - 3 hits" in output


def test_github_summary_handles_deep_skipped_or_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "missing-deep")

    missing_exit = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/missing-deep",
        ]
    )
    missing_output = capsys.readouterr().out

    write_summary(tmp_path, "skipped-deep")
    write_deep_summary(tmp_path, "skipped-deep", skipped=True)
    skipped_exit = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            ".qa-z/runs/skipped-deep",
        ]
    )
    skipped_output = capsys.readouterr().out

    assert missing_exit == 0
    assert "**Deep:** not run" in missing_output
    assert "## Deep QA" not in missing_output
    assert skipped_exit == 0
    assert "**Deep:** passed" in skipped_output
    assert "## Deep QA" in skipped_output
    assert "- Status: passed" in skipped_output
    assert "- Findings: 0" in skipped_output
    assert "- Mode: skipped" in skipped_output
