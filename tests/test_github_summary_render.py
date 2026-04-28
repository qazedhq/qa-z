"""Behavior tests for GitHub summary core render and CLI surfaces."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_z.artifacts import RunSource
from qa_z.cli import main
from qa_z.diffing.models import ChangedFile
from qa_z.reporters.github_summary import render_github_summary
from qa_z.runners.models import CheckResult, RunSummary, SelectionSummary
from tests.github_summary_test_support import (
    write_config,
    write_contract,
    write_summary,
)


def build_failed_fast_summary(root: Path) -> tuple[RunSummary, RunSource]:
    """Build a compact failed fast summary for direct render tests."""
    summary = RunSummary(
        mode="fast",
        contract_path="qa/contracts/auth.md",
        project_root=str(root),
        status="failed",
        started_at="2026-04-11T17:38:52Z",
        finished_at="2026-04-11T17:39:11Z",
        artifact_dir=".qa-z/runs/ci/fast",
        schema_version=2,
        selection=SelectionSummary(
            mode="smart",
            input_source="cli_diff",
            changed_files=[
                ChangedFile(
                    path="src/qa_z/cli.py",
                    old_path="src/qa_z/cli.py",
                    status="modified",
                    additions=8,
                    deletions=2,
                    language="python",
                    kind="source",
                )
            ],
            full_checks=["py_type"],
            targeted_checks=["py_lint", "py_test"],
            skipped_checks=["ts_lint"],
        ),
        checks=[
            CheckResult(
                id="py_type",
                tool="mypy",
                command=["mypy", "src", "tests"],
                kind="typecheck",
                status="failed",
                exit_code=1,
                duration_ms=941,
                execution_mode="full",
                selection_reason="type checks run full",
                message="mypy exited with code 1.",
            )
        ],
    )
    run_source = RunSource(
        run_dir=root / ".qa-z" / "runs" / "ci",
        fast_dir=root / ".qa-z" / "runs" / "ci" / "fast",
        summary_path=root / ".qa-z" / "runs" / "ci" / "fast" / "summary.json",
    )
    return summary, run_source


def test_github_summary_renders_compact_failed_run() -> None:
    root = Path("/repo")
    summary, run_source = build_failed_fast_summary(root)

    markdown = render_github_summary(summary=summary, run_source=run_source, root=root)

    assert "# QA-Z Summary" in markdown
    assert "**Fast:** failed" in markdown
    assert "**Deep:** not run" in markdown
    assert "**Selection:** smart" in markdown
    assert "## Fast QA" in markdown
    assert "- Passed: 0" in markdown
    assert "- Failed: 1" in markdown
    assert "- `py_type` - full - mypy exited with code 1." in markdown
    assert "- `src/qa_z/cli.py`" in markdown
    assert "- Review packet: `.qa-z/runs/ci/review/review.md`" in markdown
    assert "- Repair prompt: `.qa-z/runs/ci/repair/prompt.md`" in markdown
    assert "Repair Session Outcome" not in markdown


def test_github_summary_cli_writes_output_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    output_path = tmp_path / ".qa-z" / "runs" / "ci" / "github-summary.md"

    exit_code = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-run",
            "latest",
            "--output",
            str(output_path),
        ]
    )
    stdout = capsys.readouterr().out

    assert exit_code == 0
    assert "# QA-Z Summary" in stdout
    assert output_path.exists()
    assert "## Failed Checks" in output_path.read_text(encoding="utf-8")
    assert "Repair Session Outcome" not in stdout


def test_github_summary_cli_reports_missing_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    exit_code = main(["github-summary", "--path", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 4
    assert "source not found" in output
