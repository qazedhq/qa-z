"""Behavior tests for the local evidence summary navigator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main
from tests.github_summary_test_support import (
    write_config,
    write_contract,
    write_grouped_deep_summary,
    write_summary,
)


def read_json_stdout(capsys: pytest.CaptureFixture[str]) -> dict[str, object]:
    return json.loads(capsys.readouterr().out)


def write_repair_prompt(tmp_path: Path, run_id: str) -> None:
    repair_dir = tmp_path / ".qa-z" / "runs" / run_id / "repair"
    repair_dir.mkdir(parents=True, exist_ok=True)
    (repair_dir / "prompt.md").write_text("# Repair Prompt\n", encoding="utf-8")
    (repair_dir / "codex.md").write_text("# Codex Repair\n", encoding="utf-8")


def write_verify_report(tmp_path: Path, run_id: str) -> None:
    verify_dir = tmp_path / ".qa-z" / "runs" / run_id / "verify"
    verify_dir.mkdir(parents=True, exist_ok=True)
    (verify_dir / "report.md").write_text(
        "# QA-Z Repair Verification\n", encoding="utf-8"
    )
    (verify_dir / "summary.json").write_text(
        json.dumps(
            {
                "kind": "qa_z.verify_summary",
                "schema_version": 1,
                "verdict": "improved",
                "repair_improved": True,
            }
        ),
        encoding="utf-8",
    )


def prepare_failed_run(tmp_path: Path, run_id: str = "baseline") -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, run_id)


def test_summary_json_reports_full_evidence_navigator(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_id = "baseline"
    prepare_failed_run(tmp_path, run_id)
    write_grouped_deep_summary(tmp_path, run_id)
    write_repair_prompt(tmp_path, run_id)
    write_verify_report(tmp_path, run_id)

    exit_code = main(
        ["summary", "--path", str(tmp_path), "--from-run", "latest", "--json"]
    )
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert set(payload) >= {
        "status",
        "verdict",
        "run_dir",
        "evidence",
        "top_findings",
        "repair_prompt",
        "verify_report",
        "next_actions",
        "warnings",
    }
    assert payload["status"] == "failed"
    assert payload["verdict"] == "do_not_merge"
    assert payload["run_dir"] == ".qa-z/runs/baseline"
    evidence = payload["evidence"]
    assert isinstance(evidence, dict)
    assert evidence["fast_summary"]["path"] == ".qa-z/runs/baseline/fast/summary.json"
    assert evidence["deep_summary"]["exists"] is True
    assert payload["repair_prompt"]["path"] == ".qa-z/runs/baseline/repair/prompt.md"
    assert payload["repair_prompt"]["exists"] is True
    assert payload["verify_report"]["path"] == ".qa-z/runs/baseline/verify/report.md"
    assert payload["verify_report"]["exists"] is True
    assert payload["top_findings"]


def test_summary_handles_no_run_without_crashing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    exit_code = main(
        ["summary", "--path", str(tmp_path), "--from-run", "latest", "--json"]
    )
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "missing"
    assert payload["verdict"] == "no_run"
    assert payload["run_dir"] is None
    assert payload["warnings"]
    assert any("qa-z guard" in action for action in payload["next_actions"])


def test_summary_warns_when_deep_summary_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prepare_failed_run(tmp_path)

    exit_code = main(
        ["summary", "--path", str(tmp_path), "--from-run", "latest", "--json"]
    )
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "warning"
    evidence = payload["evidence"]
    assert isinstance(evidence, dict)
    assert evidence["deep_summary"]["exists"] is False
    assert any("deep" in warning.lower() for warning in payload["warnings"])
    assert any(
        "qa-z deep --from-run latest" in action for action in payload["next_actions"]
    )


def test_summary_points_to_repair_prompt_and_then_verify(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prepare_failed_run(tmp_path)
    write_grouped_deep_summary(tmp_path, "baseline")

    exit_code = main(
        ["summary", "--path", str(tmp_path), "--from-run", "latest", "--json"]
    )
    missing_repair = read_json_stdout(capsys)

    assert exit_code == 0
    assert missing_repair["repair_prompt"]["exists"] is False
    assert any(
        "qa-z repair-prompt" in action for action in missing_repair["next_actions"]
    )

    write_repair_prompt(tmp_path, "baseline")

    exit_code = main(
        ["summary", "--path", str(tmp_path), "--from-run", "latest", "--json"]
    )
    has_repair = read_json_stdout(capsys)

    assert exit_code == 0
    assert has_repair["repair_prompt"]["exists"] is True
    assert any(
        "qa-z verify --baseline-run latest --rerun" in action
        for action in has_repair["next_actions"]
    )


def test_summary_human_output_includes_next_actions(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prepare_failed_run(tmp_path)

    exit_code = main(["summary", "--path", str(tmp_path), "--from-run", "latest"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "QA-Z Summary:" in output
    assert "Next actions:" in output
    assert "qa-z deep --from-run latest" in output


def test_summary_warns_when_latest_manifest_is_stale(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prepare_failed_run(tmp_path, "fallback")
    manifest = tmp_path / ".qa-z" / "runs" / "latest-run.json"
    manifest.write_text(json.dumps({"run_dir": ".qa-z/runs/missing"}), encoding="utf-8")

    exit_code = main(
        ["summary", "--path", str(tmp_path), "--from-run", "latest", "--json"]
    )
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["run_dir"] == ".qa-z/runs/fallback"
    assert any("latest-run.json" in warning for warning in payload["warnings"])


def test_summary_and_github_summary_agree_on_failed_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    prepare_failed_run(tmp_path)

    summary_exit = main(
        ["summary", "--path", str(tmp_path), "--from-run", "latest", "--json"]
    )
    payload = read_json_stdout(capsys)

    github_exit = main(
        ["github-summary", "--path", str(tmp_path), "--from-run", "latest"]
    )
    github_output = capsys.readouterr().out

    assert summary_exit == 0
    assert github_exit == 0
    assert payload["verdict"] == "do_not_merge"
    assert "**Fast:** failed" in github_output
