"""Tests for qa-z doctor config validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

from qa_z.cli import main
from qa_z.config import EXAMPLE_CONFIG


@pytest.fixture(autouse=True)
def stable_doctor_tool_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep config-validation tests focused on config issues, not host tools."""
    monkeypatch.setattr("qa_z.doctor.find_executable", lambda name: name)


def write_yaml(root: Path, data: object) -> None:
    root.joinpath("qa-z.yaml").write_text(
        yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
    )


def write_yaml_with_value(root: Path, path: str, value: object) -> None:
    data: dict[str, Any] = {
        "project": {"name": "demo"},
        "contracts": {"output_dir": "qa/contracts"},
    }
    current = data
    parts = path.split(".")
    for part in parts[:-1]:
        next_value = current.setdefault(part, {})
        if not isinstance(next_value, dict):
            raise AssertionError(f"Cannot set nested config under {path}")
        current = cast(dict[str, Any], next_value)
    current[parts[-1]] = value
    write_yaml(root, data)


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


def test_doctor_fails_for_non_boolean_check_enabled(
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
                        "enabled": "false",
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
    assert payload["errors"][0]["code"] == "invalid_check_enabled"
    assert payload["errors"][0]["path"] == "fast.checks[0].enabled"


def test_doctor_fails_for_invalid_no_tests_policy(
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
                        "run": ["python", "-m", "pytest"],
                        "kind": "test",
                        "no_tests": "ignore",
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_check_no_tests"
    assert payload["errors"][0]["path"] == "fast.checks[0].no_tests"


@pytest.mark.parametrize("kind", ["", "   ", ["test"], True])
def test_doctor_fails_for_invalid_check_kind(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    kind: object,
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
                        "run": ["python", "-m", "pytest"],
                        "kind": kind,
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_check_kind"
    assert payload["errors"][0]["path"] == "fast.checks[0].kind"


@pytest.mark.parametrize("semgrep", ["auto", ["auto"], True])
def test_doctor_fails_for_invalid_semgrep_policy_section(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    semgrep: object,
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "deep": {
                "checks": [
                    {
                        "id": "sg_scan",
                        "run": ["semgrep", "--json"],
                        "kind": "static-analysis",
                        "semgrep": semgrep,
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_semgrep_policy"
    assert payload["errors"][0]["path"] == "deep.checks[0].semgrep"


@pytest.mark.parametrize("config", ["", "   ", ["auto"], True])
def test_doctor_fails_for_invalid_semgrep_config_value(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    config: object,
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "deep": {
                "checks": [
                    {
                        "id": "sg_scan",
                        "run": ["semgrep", "--json"],
                        "kind": "static-analysis",
                        "semgrep": {"config": config},
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_semgrep_config"
    assert payload["errors"][0]["path"] == "deep.checks[0].semgrep.config"


@pytest.mark.parametrize(
    "field",
    ["fail_on_severity", "ignore_rules", "exclude_paths"],
)
@pytest.mark.parametrize("value", ["ERROR", ["ERROR", ""], ["ERROR", True]])
def test_doctor_fails_for_invalid_semgrep_string_lists(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    field: str,
    value: object,
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "deep": {
                "checks": [
                    {
                        "id": "sg_scan",
                        "run": ["semgrep", "--json"],
                        "kind": "static-analysis",
                        "semgrep": {field: value},
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == f"invalid_semgrep_{field}"
    assert payload["errors"][0]["path"] == f"deep.checks[0].semgrep.{field}"


def test_doctor_fails_for_unknown_semgrep_blocking_severity(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "deep": {
                "checks": [
                    {
                        "id": "sg_scan",
                        "run": ["semgrep", "--json"],
                        "kind": "static-analysis",
                        "semgrep": {"fail_on_severity": ["CRITICAL"]},
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_semgrep_fail_on_severity"
    assert payload["errors"][0]["path"] == (
        "deep.checks[0].semgrep.fail_on_severity[0]"
    )


def test_doctor_fails_for_unknown_semgrep_policy_key(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "deep": {
                "checks": [
                    {
                        "id": "sg_scan",
                        "run": ["semgrep", "--json"],
                        "kind": "static-analysis",
                        "semgrep": {"fail_on_severty": ["ERROR"]},
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "unknown_semgrep_policy_key"
    assert payload["errors"][0]["path"] == "deep.checks[0].semgrep.fail_on_severty"


def test_doctor_warns_when_semgrep_policy_is_not_attached_to_sg_scan(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "deep": {
                "checks": [
                    {
                        "id": "custom_semgrep",
                        "run": ["semgrep", "--json"],
                        "kind": "static-analysis",
                        "semgrep": {"config": "auto"},
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "warning"
    assert payload["warnings"][0]["code"] == "ignored_semgrep_policy"
    assert payload["warnings"][0]["path"] == "deep.checks[0].semgrep"


def test_doctor_fails_for_boolean_timeout_seconds(
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
                        "run": ["python", "-m", "pytest"],
                        "kind": "test",
                        "timeout_seconds": True,
                    }
                ]
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_timeout"
    assert payload["errors"][0]["path"] == "fast.checks[0].timeout_seconds"


def test_doctor_fails_for_non_boolean_fast_strict_no_tests(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {"strict_no_tests": "false", "checks": ["py_test"]},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_fast_strict_no_tests"
    assert payload["errors"][0]["path"] == "fast.strict_no_tests"


def test_doctor_fails_for_non_boolean_missing_tool_policies(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "fast": {"fail_on_missing_tool": "false", "checks": ["py_test"]},
            "deep": {"fail_on_missing_tool": "true", "checks": ["sg_scan"]},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert {(error["code"], error["path"]) for error in payload["errors"]} == {
        ("invalid_fast_fail_on_missing_tool", "fast.fail_on_missing_tool"),
        ("invalid_deep_fail_on_missing_tool", "deep.fail_on_missing_tool"),
    }


def test_doctor_fails_for_non_mapping_reporters_section(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "reporters": ["markdown"],
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_reporters_type"
    assert payload["errors"][0]["path"] == "reporters"


def test_doctor_fails_for_non_boolean_markdown_reporter(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "reporters": {"markdown": "false"},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_reporters_markdown"
    assert payload["errors"][0]["path"] == "reporters.markdown"


@pytest.mark.parametrize(
    "section",
    ["project", "contracts", "fast", "deep", "checks", "gates", "adapters"],
)
def test_doctor_fails_for_non_mapping_core_sections(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    section: str,
) -> None:
    data: dict[str, object] = {
        "project": {"name": "demo"},
        "contracts": {"output_dir": "qa/contracts"},
    }
    data[section] = ["not-a-mapping"]
    write_yaml(tmp_path, data)

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == f"invalid_{section}_type"
    assert payload["errors"][0]["path"] == section


@pytest.mark.parametrize("name", ["", "   ", ["qa-z"], True])
def test_doctor_fails_for_invalid_project_name(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    name: object,
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": name},
            "contracts": {"output_dir": "qa/contracts"},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_project_name"
    assert payload["errors"][0]["path"] == "project.name"


@pytest.mark.parametrize("output_dir", ["", "   ", ["qa/contracts"], True])
def test_doctor_fails_for_invalid_contracts_output_dir(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    output_dir: object,
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": output_dir},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_contracts_output_dir"
    assert payload["errors"][0]["path"] == "contracts.output_dir"


@pytest.mark.parametrize("output_dir", ["", "   ", ["runs"], True])
def test_doctor_fails_for_invalid_fast_output_dir(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    output_dir: object,
) -> None:
    write_yaml_with_value(tmp_path, "fast.output_dir", output_dir)

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_fast_output_dir"
    assert payload["errors"][0]["path"] == "fast.output_dir"


@pytest.mark.parametrize("default_contract", ["", "   ", ["latest"], True])
def test_doctor_fails_for_invalid_fast_default_contract(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    default_contract: object,
) -> None:
    write_yaml_with_value(tmp_path, "fast.default_contract", default_contract)

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_fast_default_contract"
    assert payload["errors"][0]["path"] == "fast.default_contract"


@pytest.mark.parametrize(
    "path", ["fast.selection", "deep.selection", "checks.selection"]
)
def test_doctor_fails_for_non_mapping_selection_sections(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    path: str,
) -> None:
    write_yaml_with_value(tmp_path, path, ["smart"])

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == f"invalid_{path.replace('.', '_')}"
    assert payload["errors"][0]["path"] == path


def test_doctor_warns_for_ignored_legacy_checks_selection_mode(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "checks": {"selection": {"mode": "diff-aware", "max_changed_files": 40}},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "warning"
    assert payload["warnings"][0]["code"] == "legacy_checks_selection_mode"
    assert payload["warnings"][0]["path"] == "checks.selection.mode"


@pytest.mark.parametrize(
    "path", ["fast.selection.default_mode", "deep.selection.default_mode"]
)
@pytest.mark.parametrize("default_mode", ["targeted", "", True])
def test_doctor_fails_for_invalid_selection_default_modes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    path: str,
    default_mode: object,
) -> None:
    write_yaml_with_value(tmp_path, path, default_mode)

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == f"invalid_{path.replace('.', '_')}"
    assert payload["errors"][0]["path"] == path


@pytest.mark.parametrize(
    "path",
    [
        "fast.selection.full_run_threshold",
        "deep.selection.full_run_threshold",
        "checks.selection.max_changed_files",
    ],
)
@pytest.mark.parametrize("threshold", [-1, "many", True])
def test_doctor_fails_for_invalid_selection_thresholds(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    path: str,
    threshold: object,
) -> None:
    write_yaml_with_value(tmp_path, path, threshold)

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == f"invalid_{path.replace('.', '_')}"
    assert payload["errors"][0]["path"] == path


@pytest.mark.parametrize(
    "path",
    [
        "project.languages",
        "project.roots",
        "project.critical_paths",
        "contracts.sources",
        "contracts.required_sections",
        "fast.selection.high_risk_paths",
        "deep.selection.high_risk_paths",
        "deep.selection.exclude_paths",
        "gates.escalate_on",
        "gates.block_on",
    ],
)
@pytest.mark.parametrize("value", ["src", ["src", ""], ["src", True]])
def test_doctor_fails_for_invalid_string_list_options(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    path: str,
    value: object,
) -> None:
    write_yaml_with_value(tmp_path, path, value)

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == f"invalid_{path.replace('.', '_')}"
    assert payload["errors"][0]["path"] == path


@pytest.mark.parametrize(
    "path",
    [
        "reporters.json",
        "reporters.sarif",
        "reporters.github_annotations",
        "reporters.repair_packet",
        "gates.require_human_review",
    ],
)
def test_doctor_fails_for_non_boolean_feature_flags(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    path: str,
) -> None:
    write_yaml_with_value(tmp_path, path, "false")

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == f"invalid_{path.replace('.', '_')}"
    assert payload["errors"][0]["path"] == path


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


def test_doctor_warns_when_adapter_instruction_path_is_directory(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "agent-docs").mkdir()
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "adapters": {
                "codex": {
                    "enabled": True,
                    "instructions_file": "agent-docs",
                }
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "warning"
    assert payload["warnings"][0]["code"] == "adapter_instruction_file_not_file"
    assert payload["warnings"][0]["path"] == "adapters.codex.instructions_file"
    assert "qa-z init --with-agent-templates" in payload["suggestions"]


def test_doctor_fails_for_non_boolean_adapter_enabled(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "adapters": {
                "codex": {
                    "enabled": "false",
                    "instructions_file": "AGENTS.md",
                }
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_adapter_enabled"
    assert payload["errors"][0]["path"] == "adapters.codex.enabled"


def test_doctor_fails_for_non_mapping_adapter_entry(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "adapters": {"codex": True},
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_adapter_type"
    assert payload["errors"][0]["path"] == "adapters.codex"


@pytest.mark.parametrize("instructions_file", ["", "   ", ["AGENTS.md"], True])
def test_doctor_fails_for_invalid_adapter_instructions_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    instructions_file: object,
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "adapters": {
                "codex": {
                    "enabled": True,
                    "instructions_file": instructions_file,
                }
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "invalid_adapter_instructions_file"
    assert payload["errors"][0]["path"] == "adapters.codex.instructions_file"


def test_doctor_allows_disabled_adapter_with_placeholder_instruction_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(
        tmp_path,
        {
            "project": {"name": "demo"},
            "contracts": {"output_dir": "qa/contracts"},
            "adapters": {
                "codex": {
                    "enabled": False,
                    "instructions_file": True,
                }
            },
        },
    )

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "passed"


def test_doctor_fails_when_config_root_is_not_mapping(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_yaml(tmp_path, ["not-a-mapping"])

    exit_code = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "failed"
    assert payload["errors"][0]["code"] == "config_error"


def test_doctor_strict_returns_nonzero_for_warnings(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "qa-z.yaml").write_text(EXAMPLE_CONFIG, encoding="utf-8")

    exit_code = main(["doctor", "--path", str(tmp_path), "--strict"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "qa-z doctor: warning" in output
