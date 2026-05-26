"""Behavior tests for the QA-Z readiness scorecard."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from qa_z.cli import main
from tests.github_summary_test_support import (
    write_contract,
    write_deep_summary,
    write_summary,
)


def read_json_stdout(capsys: pytest.CaptureFixture[str]) -> dict[str, Any]:
    return json.loads(capsys.readouterr().out)


def write_scorecard_config(
    tmp_path: Path, *, languages: list[str] | None = None
) -> None:
    config = {
        "project": {
            "name": "scorecard-test",
            "languages": languages or ["python"],
            "roots": ["src", "tests"],
        },
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "checks": [
                {
                    "id": "py_test",
                    "enabled": True,
                    "run": ["pytest", "-q"],
                    "kind": "test",
                }
            ],
        },
        "deep": {
            "checks": [
                {
                    "id": "sg_scan",
                    "enabled": True,
                    "run": ["semgrep", "--config", "auto", "--json"],
                    "kind": "static-analysis",
                    "semgrep": {"config": "auto", "fail_on_severity": ["ERROR"]},
                }
            ]
        },
        "reporters": {"markdown": True, "json": True, "repair_packet": True},
        "adapters": {"codex": {"enabled": True, "instructions_file": "AGENTS.md"}},
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    (tmp_path / "AGENTS.md").write_text("# Agent Instructions\n", encoding="utf-8")


def write_repair_and_verify(tmp_path: Path, run_id: str) -> None:
    repair_dir = tmp_path / ".qa-z" / "runs" / run_id / "repair"
    verify_dir = tmp_path / ".qa-z" / "runs" / run_id / "verify"
    repair_dir.mkdir(parents=True, exist_ok=True)
    verify_dir.mkdir(parents=True, exist_ok=True)
    (repair_dir / "prompt.md").write_text("# Repair Prompt\n", encoding="utf-8")
    (verify_dir / "report.md").write_text("# Verify Report\n", encoding="utf-8")
    (verify_dir / "summary.json").write_text(
        json.dumps({"kind": "qa_z.verify_summary", "verdict": "improved"}),
        encoding="utf-8",
    )


def write_github_workflow(tmp_path: Path) -> None:
    workflow = tmp_path / ".github" / "workflows" / "qa-z.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "\n".join(
            [
                "name: QA-Z",
                "permissions:",
                "  contents: read",
                "jobs:",
                "  qa-z:",
                "    steps:",
                "      - run: python -m qa_z guard --adapter codex",
                "",
            ]
        ),
        encoding="utf-8",
    )


def prepare_healthy_repo(tmp_path: Path) -> None:
    run_id = "baseline"
    write_scorecard_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, run_id)
    write_deep_summary(tmp_path, run_id, skipped=True)
    write_repair_and_verify(tmp_path, run_id)
    write_github_workflow(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "scorecard-test"\n', encoding="utf-8"
    )


def dimension(payload: dict[str, Any], dimension_id: str) -> dict[str, Any]:
    dimensions = payload["dimensions"]
    assert isinstance(dimensions, list)
    for item in dimensions:
        if item["id"] == dimension_id:
            return item
    raise AssertionError(f"missing scorecard dimension: {dimension_id}")


def test_scorecard_json_reports_healthy_repo(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_healthy_repo(tmp_path)
    monkeypatch.setattr("qa_z.scorecard.shutil.which", lambda name: "/usr/bin/semgrep")

    exit_code = main(["scorecard", "--path", str(tmp_path), "--json"])
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["kind"] == "qa_z.scorecard"
    assert payload["schema_version"] == 1
    assert payload["status"] == "ready"
    assert set(payload) >= {
        "status",
        "version",
        "dimensions",
        "summary",
        "next_actions",
        "warnings",
    }
    assert dimension(payload, "project_config")["status"] == "ready"
    assert dimension(payload, "profile")["status"] == "ready"
    assert dimension(payload, "fast_checks")["status"] == "ready"
    assert dimension(payload, "deep_semgrep")["status"] == "ready"
    assert dimension(payload, "repair_prompt")["status"] == "ready"
    assert dimension(payload, "verify")["status"] == "ready"
    assert dimension(payload, "github_action")["status"] == "ready"
    assert dimension(payload, "evidence_freshness")["status"] == "ready"


def test_scorecard_blocks_when_qa_z_yaml_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(["scorecard", "--path", str(tmp_path), "--json"])
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "blocked"
    config = dimension(payload, "project_config")
    assert config["status"] == "blocked"
    assert "qa-z.yaml" in config["message"]
    assert any("qa-z init" in action for action in payload["next_actions"])


def test_scorecard_warns_when_semgrep_is_missing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_healthy_repo(tmp_path)
    monkeypatch.setattr("qa_z.scorecard.shutil.which", lambda name: None)

    exit_code = main(["scorecard", "--path", str(tmp_path), "--json"])
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "warning"
    semgrep = dimension(payload, "deep_semgrep")
    assert semgrep["status"] == "warning"
    assert "Semgrep not found" in semgrep["message"]
    assert any("Install Semgrep" in action for action in payload["next_actions"])


def test_scorecard_json_schema_stays_stable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_healthy_repo(tmp_path)
    monkeypatch.setattr("qa_z.scorecard.shutil.which", lambda name: "/usr/bin/semgrep")

    exit_code = main(["scorecard", "--path", str(tmp_path), "--json"])
    payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert list(payload) == [
        "kind",
        "schema_version",
        "status",
        "version",
        "root",
        "generated_at",
        "dimensions",
        "summary",
        "next_actions",
        "warnings",
    ]
    for item in payload["dimensions"]:
        assert list(item) == [
            "id",
            "status",
            "message",
            "evidence",
            "suggestion",
            "next_actions",
        ]


def test_scorecard_human_output_includes_next_actions(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepare_healthy_repo(tmp_path)
    monkeypatch.setattr("qa_z.scorecard.shutil.which", lambda name: None)

    exit_code = main(["scorecard", "--path", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "QA-Z Scorecard: warning" in output
    assert "WARN deep/Semgrep: Semgrep not found" in output
    assert "Next actions:" in output


def test_scorecard_does_not_create_runtime_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_scorecard_config(tmp_path)
    monkeypatch.setattr("qa_z.scorecard.shutil.which", lambda name: None)

    exit_code = main(["scorecard", "--path", str(tmp_path), "--json"])
    _payload = read_json_stdout(capsys)

    assert exit_code == 0
    assert not (tmp_path / ".qa-z").exists()
