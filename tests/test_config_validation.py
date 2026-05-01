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


def test_doctor_fails_for_unsafe_check_ids(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {
                "checks": [
                    {
                        "id": "../escape",
                        "run": ["python", "-m", "pytest"],
                        "kind": "test",
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_check_id"
    assert payload["errors"][0]["path"] == "fast.checks[0].id"


def test_doctor_fails_for_duplicate_check_ids(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {
                "checks": [
                    {"id": "custom_gate", "run": ["python", "-c", ""]},
                    {"id": "custom_gate", "run": ["python", "-c", ""]},
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "duplicate_check_id"
    assert payload["errors"][0]["path"] == "fast.checks[1].id"


def test_doctor_fails_for_empty_check_executable(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {
                "checks": [
                    {
                        "id": "custom_gate",
                        "run": [""],
                        "kind": "test",
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_check_run"
    assert payload["errors"][0]["path"] == "fast.checks[0].run"


def test_doctor_allows_empty_string_command_arguments(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {
                "checks": [
                    {
                        "id": "custom_gate",
                        "run": ["python", "-c", ""],
                        "kind": "test",
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "passed"


def test_doctor_allows_disabled_custom_checks_without_run(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {"checks": [{"id": "fast_placeholder", "enabled": False}]},
            "deep": {"checks": [{"id": "deep_placeholder", "enabled": False}]},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "passed"


def test_doctor_detects_duplicate_check_aliases(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "deep": {"checks": ["semgrep", {"id": "sg_scan"}]},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "duplicate_check_id"
    assert payload["errors"][0]["path"] == "deep.checks[1].id"


def test_doctor_fails_unknown_string_checks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {"checks": ["unknown_gate"]},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "unknown_check_id"
    assert payload["errors"][0]["path"] == "fast.checks[0]"


def test_doctor_validates_legacy_deep_check_items(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "checks": {"deep": ["unknown_gate"]},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["warnings"][0]["code"] == "legacy_checks_deep"
    assert payload["errors"][0]["code"] == "unknown_check_id"
    assert payload["errors"][0]["path"] == "checks.deep[0]"


def test_doctor_ignores_legacy_deep_checks_when_modern_deep_checks_exist(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "deep": {"checks": ["sg_scan"]},
            "checks": {"deep": ["unknown_gate"]},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "warning"
    assert payload["warnings"][0]["code"] == "legacy_checks_deep"
    assert payload["errors"] == []


def test_doctor_ignores_legacy_fast_checks_when_modern_fast_checks_exist(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {"checks": ["py_test"]},
            "checks": {"fast": {"id": "unknown_gate"}},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "warning"
    assert payload["warnings"][0]["code"] == "legacy_checks_fast"
    assert payload["errors"] == []


def test_doctor_requires_run_for_custom_mapping_checks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "deep": {"checks": [{"id": "custom_deep"}]},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "missing_check_run"
    assert payload["errors"][0]["path"] == "deep.checks[0].run"


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
