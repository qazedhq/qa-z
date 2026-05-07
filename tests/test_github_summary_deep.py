"""Behavior tests for GitHub summary deep-context rendering."""

from __future__ import annotations

import json
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


def test_github_summary_surfaces_deep_scan_warnings_without_findings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "scan-warning")
    write_deep_summary(tmp_path, "scan-warning")
    deep_summary_path = (
        tmp_path / ".qa-z" / "runs" / "scan-warning" / "deep" / "summary.json"
    )
    payload = json.loads(deep_summary_path.read_text(encoding="utf-8"))
    payload["status"] = "passed"
    payload["diagnostics"] = {
        "scan_quality": {
            "status": "warning",
            "warning_count": 2,
            "warning_types": ["Fixpoint timeout"],
            "warning_paths": ["src/app.py", "src/db.py"],
            "check_ids": ["sg_scan"],
        }
    }
    payload["checks"][0].update(
        {
            "status": "passed",
            "findings_count": 0,
            "blocking_findings_count": 0,
            "filtered_findings_count": 0,
            "severity_summary": {},
            "findings": [],
        }
    )
    deep_summary_path.write_text(json.dumps(payload), encoding="utf-8")

    exit_code = main(
        ["github-summary", "--path", str(tmp_path), "--from-run", "latest"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "- Scan quality: warning (2 warnings)" in output
    assert "- Warning types: Fixpoint timeout" in output
    assert "- Warning paths: `src/app.py`, `src/db.py`" in output
    assert "- Warning checks: sg_scan" in output


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
