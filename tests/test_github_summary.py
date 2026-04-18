"""Tests for GitHub summary rendering."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.cli import main
from qa_z.reporters.github_summary import render_github_summary


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def test_github_summary_renders_verify_publish_section(tmp_path: Path) -> None:
    verify_path = tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json"
    write_json(
        verify_path,
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "repair_improved": True,
            "verdict": "improved",
            "blocking_before": 1,
            "blocking_after": 0,
            "resolved_count": 1,
            "remaining_issue_count": 0,
            "new_issue_count": 0,
            "regression_count": 0,
            "not_comparable_count": 0,
        },
    )

    markdown = render_github_summary(root=tmp_path, from_verify=str(verify_path))

    assert "## QA-Z Summary" in markdown
    assert "# QA-Z Verification Summary" in markdown
    assert "- Verdict: improved" in markdown


def test_github_summary_can_render_run_artifact(tmp_path: Path) -> None:
    fast_path = tmp_path / ".qa-z" / "runs" / "ci" / "fast" / "summary.json"
    write_json(
        fast_path,
        {
            "schema_version": 2,
            "mode": "fast",
            "contract_path": None,
            "project_root": str(tmp_path),
            "status": "passed",
            "started_at": "2026-04-14T00:00:00Z",
            "finished_at": "2026-04-14T00:00:01Z",
            "artifact_dir": ".qa-z/runs/ci/fast",
            "checks": [],
            "totals": {"passed": 0, "failed": 0, "skipped": 0, "warning": 0},
        },
    )

    markdown = render_github_summary(root=tmp_path, from_run=".qa-z/runs/ci")

    assert "## QA-Z Summary" in markdown
    assert "- Run mode: fast" in markdown
    assert "- Status: passed" in markdown


def test_github_summary_cli_outputs_markdown_and_json(tmp_path: Path, capsys) -> None:
    verify_path = tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json"
    write_json(
        verify_path,
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "repair_improved": True,
            "verdict": "improved",
            "blocking_before": 1,
            "blocking_after": 0,
            "resolved_count": 1,
            "remaining_issue_count": 0,
            "new_issue_count": 0,
            "regression_count": 0,
            "not_comparable_count": 0,
        },
    )

    text_exit = main(
        ["github-summary", "--path", str(tmp_path), "--from-verify", str(verify_path)]
    )
    text = capsys.readouterr().out
    json_exit = main(
        [
            "github-summary",
            "--path",
            str(tmp_path),
            "--from-verify",
            str(verify_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert text_exit == 0
    assert "## QA-Z Summary" in text
    assert json_exit == 0
    assert payload["verdict"] == "improved"
