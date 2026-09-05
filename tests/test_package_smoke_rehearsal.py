"""Tests for the no-upload package smoke rehearsal helper."""

from __future__ import annotations

import json
import subprocess
import sys

from tests.package_smoke_rehearsal_test_support import FakeRehearsalRunner
from tests.package_smoke_rehearsal_test_support import load_rehearsal_module


def _write_dist(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / "qa_z-0.9.8a0-py3-none-any.whl"
    sdist = dist / "qa_z-0.9.8a0.tar.gz"
    wheel.write_bytes(b"fake wheel")
    sdist.write_bytes(b"fake sdist")
    return wheel, sdist


def _assert_no_upload_commands(commands: list[tuple[str, ...]]) -> None:
    forbidden = (
        "upload",
        "publish",
        "tag",
        "release create",
        "deploy",
    )
    command_text = "\n".join(" ".join(command) for command in commands)
    for text in forbidden:
        assert text not in command_text


def test_rehearsal_reports_missing_tools_as_not_run_with_no_upload(tmp_path):
    module = load_rehearsal_module()
    runner = FakeRehearsalRunner({"twine", "pipx", "uvx"})

    result = module.run_package_smoke_rehearsal(
        tmp_path,
        allow_missing_tools=True,
        runner=runner,
    )
    payload = module.result_payload(result)

    assert result.exit_code == 0
    assert result.overall_status == "PARTIAL"
    assert payload["registry_upload_executed"] is False
    assert payload["credential_inputs_loaded"] is False
    assert {check["status"] for check in payload["checks"]} == {"NOT_RUN"}
    assert {check["name"] for check in payload["checks"]} == {
        "twine_check",
        "pipx_help_smoke",
        "uvx_help_smoke",
    }
    _assert_no_upload_commands(runner.commands)


def test_rehearsal_fails_closed_when_required_tool_is_missing(tmp_path):
    module = load_rehearsal_module()
    runner = FakeRehearsalRunner({"twine"})

    result = module.run_package_smoke_rehearsal(
        tmp_path,
        allow_missing_tools=False,
        runner=runner,
    )

    assert result.exit_code == 1
    assert result.overall_status == "FAIL"
    assert result.checks[0].name == "twine_check"
    assert result.checks[0].status == "FAIL"
    assert "missing" in result.checks[0].detail
    _assert_no_upload_commands(runner.commands)


def test_rehearsal_runs_twine_pipx_and_uvx_against_built_artifacts(tmp_path):
    module = load_rehearsal_module()
    wheel, sdist = _write_dist(tmp_path)
    runner = FakeRehearsalRunner()

    result = module.run_package_smoke_rehearsal(
        tmp_path,
        wheel=wheel,
        sdist=sdist,
        runner=runner,
    )
    payload = module.result_payload(result)
    commands = [" ".join(command) for command in runner.commands]

    assert result.exit_code == 0
    assert result.overall_status == "PASS"
    assert [check["status"] for check in payload["checks"]] == [
        "PASS",
        "PASS",
        "PASS",
    ]
    assert any(
        f"{sys.executable} -m twine check {wheel} {sdist}" in command
        for command in commands
    )
    assert any(
        f"pipx run --spec {wheel} qa-z --help" in command for command in commands
    )
    assert any(f"uvx --from {wheel} qa-z --help" in command for command in commands)
    _assert_no_upload_commands(runner.commands)


def test_rehearsal_cli_can_emit_json(monkeypatch, capsys):
    module = load_rehearsal_module()

    def fake_run_package_smoke_rehearsal(_repo_root, **kwargs):
        assert kwargs["allow_missing_tools"] is True
        assert kwargs["wheel"].as_posix() == "dist/custom.whl"
        assert kwargs["sdist"].as_posix() == "dist/custom.tar.gz"
        return module.RehearsalResult(
            [module.RehearsalCheck("twine_check", "NOT_RUN", "twine missing")]
        )

    monkeypatch.setattr(
        module, "run_package_smoke_rehearsal", fake_run_package_smoke_rehearsal
    )

    exit_code = module.main(
        [
            "--wheel",
            "dist/custom.whl",
            "--sdist",
            "dist/custom.tar.gz",
            "--json",
            "--allow-missing-tools",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["overall_status"] == "PARTIAL"
    assert payload["registry_upload_executed"] is False
    assert payload["checks"] == [
        {
            "name": "twine_check",
            "status": "NOT_RUN",
            "detail": "twine missing",
        }
    ]


def test_rehearsal_subprocess_runner_strips_registry_credentials(monkeypatch, tmp_path):
    module = load_rehearsal_module()
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = list(command)
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setenv("TWINE_USERNAME", "secret-user")
    monkeypatch.setenv("TWINE_PASSWORD", "secret-password")
    monkeypatch.setenv("TWINE_API_TOKEN", "secret-token")
    monkeypatch.setenv("UV_PUBLISH_TOKEN", "secret-uv")
    support_module = module._PACKAGE_SMOKE_REHEARSAL_SUPPORT
    monkeypatch.setattr(support_module.subprocess, "run", fake_run)

    exit_code, stdout, stderr = module.subprocess_runner(
        ["pipx", "--version"], tmp_path
    )

    assert exit_code == 0
    assert stdout == "ok\n"
    assert stderr == ""
    env = captured["env"]
    assert isinstance(env, dict)
    for name in (
        "TWINE_USERNAME",
        "TWINE_PASSWORD",
        "TWINE_API_TOKEN",
        "UV_PUBLISH_TOKEN",
    ):
        assert name not in env
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"


def test_rehearsal_subprocess_runner_reports_missing_executable(monkeypatch, tmp_path):
    module = load_rehearsal_module()

    def fake_run(command, **_kwargs):
        raise FileNotFoundError(command[0])

    support_module = module._PACKAGE_SMOKE_REHEARSAL_SUPPORT
    monkeypatch.setattr(support_module.subprocess, "run", fake_run)

    exit_code, stdout, stderr = module.subprocess_runner(
        ["pipx", "--version"], tmp_path
    )

    assert exit_code == 127
    assert stdout == ""
    assert "pipx" in stderr
