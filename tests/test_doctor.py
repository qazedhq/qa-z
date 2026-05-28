"""Environment diagnostics for qa-z doctor."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from qa_z.cli import main
from qa_z.config import EXAMPLE_CONFIG
from qa_z.doctor import DoctorCheck


REPO_ROOT = Path(__file__).resolve().parents[1]


def write_ready_config(root: Path) -> None:
    root.joinpath("qa-z.yaml").write_text(EXAMPLE_CONFIG, encoding="utf-8")
    root.joinpath("AGENTS.md").write_text("# Agents\n", encoding="utf-8")
    root.joinpath("CLAUDE.md").write_text("# Claude\n", encoding="utf-8")


def fake_tool_lookup(*, semgrep: bool = True, git: bool = True):
    def lookup(name: str) -> str | None:
        if name == "semgrep":
            return "semgrep" if semgrep else None
        if name == "git":
            return "git" if git else None
        return name

    return lookup


def run_doctor_json(
    args: list[str],
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, dict[str, Any]]:
    exit_code = main(["doctor", "--json", *args])
    payload = json.loads(capsys.readouterr().out)
    return exit_code, payload


def check_by_id(payload: dict[str, Any], check_id: str) -> dict[str, Any]:
    for check in payload["checks"]:
        if check["id"] == check_id:
            return check
    raise AssertionError(f"missing doctor check {check_id}")


def test_doctor_passes_in_normal_source_checkout(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("qa_z.doctor.find_executable", fake_tool_lookup())
    monkeypatch.setattr(
        "qa_z.doctor.runtime_artifact_check",
        lambda root: DoctorCheck(
            id="runtime.artifacts",
            status="passed",
            message=f"writable at {root / '.qa-z'}",
            evidence={"runtime_dir": str(root / ".qa-z"), "writable": True},
        ),
    )
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    exit_code, payload = run_doctor_json([], capsys)

    assert exit_code == 0
    assert payload["status"] == "passed"
    assert payload["version"] == "0.10.0b0"
    assert payload["warnings"] == []
    assert payload["errors"] == []
    assert check_by_id(payload, "runtime.python")["status"] == "passed"
    install_check = check_by_id(payload, "install.mode")
    assert install_check["status"] == "passed"
    assert "source checkout" in install_check["evidence"]["modes"]
    assert check_by_id(payload, "config.qa_z_yaml")["status"] == "passed"


def test_passed_doctor_suggests_first_run_next_actions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_ready_config(tmp_path)
    monkeypatch.setattr("qa_z.doctor.find_executable", fake_tool_lookup())

    exit_code, payload = run_doctor_json(["--path", str(tmp_path)], capsys)

    assert exit_code == 0
    assert payload["status"] == "passed"
    assert payload["next_actions"] == [
        "Run `qa-z demo auth-bug`.",
        "Run `qa-z scorecard`.",
        "Run `qa-z guard --adapter codex --deep auto --fail-on-risk`.",
    ]


def test_doctor_warns_when_qa_z_yaml_is_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("qa_z.doctor.find_executable", fake_tool_lookup())

    exit_code, payload = run_doctor_json(["--path", str(tmp_path)], capsys)

    assert exit_code == 0
    assert payload["status"] == "warning"
    config_check = check_by_id(payload, "config.qa_z_yaml")
    assert config_check["status"] == "warning"
    assert config_check["suggestion"] == "Run `qa-z init`."
    assert "qa-z init" in payload["suggestions"]
    assert payload["next_actions"][0] == "Run `qa-z init`."


def test_doctor_detects_github_actions_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_ready_config(tmp_path)
    monkeypatch.setattr("qa_z.doctor.find_executable", fake_tool_lookup())
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(tmp_path / "summary.md"))

    exit_code, payload = run_doctor_json(["--path", str(tmp_path)], capsys)

    assert exit_code == 0
    actions_check = check_by_id(payload, "environment.github_actions")
    assert actions_check["status"] == "passed"
    assert actions_check["evidence"]["github_actions"] is True
    assert actions_check["evidence"]["step_summary_present"] is True
    assert "SARIF" in actions_check["message"]


def test_doctor_handles_missing_semgrep_without_crashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_ready_config(tmp_path)
    monkeypatch.setattr("qa_z.doctor.find_executable", fake_tool_lookup(semgrep=False))

    exit_code, payload = run_doctor_json(["--path", str(tmp_path)], capsys)

    assert exit_code == 0
    assert payload["status"] == "warning"
    semgrep_check = check_by_id(payload, "tool.semgrep")
    assert semgrep_check["status"] == "warning"
    assert semgrep_check["suggestion"] == ("Install Semgrep if you want deep checks.")
    assert "deep checks may be limited" in semgrep_check["message"]
    assert "Install Semgrep if you want deep checks." in payload["next_actions"]


def test_doctor_detects_auth_bug_template_loading(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_ready_config(tmp_path)
    monkeypatch.setattr("qa_z.doctor.find_executable", fake_tool_lookup())

    _, payload = run_doctor_json(["--path", str(tmp_path)], capsys)

    template_check = check_by_id(payload, "resources.auth_bug_template")
    assert template_check["status"] == "passed"
    assert template_check["evidence"]["resource"] == (
        "templates/examples/agent-auth-bug/repo/qa-z.yaml"
    )


def test_doctor_reports_runtime_artifact_writeability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_ready_config(tmp_path)
    monkeypatch.setattr("qa_z.doctor.find_executable", fake_tool_lookup())

    _, payload = run_doctor_json(["--path", str(tmp_path)], capsys)

    artifact_check = check_by_id(payload, "runtime.artifacts")
    assert artifact_check["status"] == "passed"
    assert artifact_check["evidence"]["runtime_dir"] == str(tmp_path / ".qa-z")
    assert not (tmp_path / ".qa-z" / ".doctor-write-test").exists()


def test_doctor_json_schema_stays_stable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write_ready_config(tmp_path)
    monkeypatch.setattr("qa_z.doctor.find_executable", fake_tool_lookup())

    _, payload = run_doctor_json(["--path", str(tmp_path)], capsys)

    assert set(payload) >= {
        "status",
        "version",
        "checks",
        "warnings",
        "errors",
        "suggestions",
        "next_actions",
    }
    assert payload["checks"]
    for check in payload["checks"]:
        assert set(check) == {"id", "status", "message", "evidence", "suggestion"}


def test_doctor_human_output_includes_next_actions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("qa_z.doctor.find_executable", fake_tool_lookup(semgrep=False))

    exit_code = main(["doctor", "--path", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "QA-Z Doctor: warning" in output
    assert "WARN qa-z.yaml: missing" in output
    assert "WARN semgrep: not found; deep checks may be limited" in output
    assert "Next actions:" in output
    assert "1. Run `qa-z init`." in output
    assert "Install Semgrep if you want deep checks." in output
