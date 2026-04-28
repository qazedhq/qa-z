"""Tests for qa-z doctor config validation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from qa_z.cli import main
from qa_z.config import EXAMPLE_CONFIG


def write_yaml(root: Path, data: object) -> None:
    root.joinpath("qa-z.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )


def test_doctor_passes_valid_example_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text(EXAMPLE_CONFIG, encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# Claude\n", encoding="utf-8")

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "passed"
    assert payload["errors"] == []
    assert payload["warnings"] == []


def test_doctor_warns_for_legacy_checks_deep(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "checks": {"deep": ["security"]},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "warning"
    assert payload["warnings"][0]["code"] == "legacy_checks_deep"


def test_doctor_fails_for_non_list_fast_checks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {"checks": {"id": "py_test"}},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_checks_type"


def test_doctor_warns_for_missing_agent_instruction_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text(EXAMPLE_CONFIG, encoding="utf-8")

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "warning"
    assert {warning["code"] for warning in payload["warnings"]} == {
        "missing_instruction_file"
    }
    assert "qa-z init --with-agent-templates" in payload["suggestions"]


def test_doctor_strict_returns_nonzero_for_warnings(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text(EXAMPLE_CONFIG, encoding="utf-8")

    exit_code = main(["doctor", "--path", str(tmp_path), "--strict"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "qa-z doctor: warning" in output
