"""Tests for the alpha release artifact install-smoke helper."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from tests.alpha_release_artifact_smoke_test_support import (
    FakeSmokeRunner,
    load_smoke_module,
)


def test_artifact_smoke_installs_wheel_without_dependency_resolution(tmp_path):
    module = load_smoke_module()
    artifact = tmp_path / "qa_z-0.9.8a0-py3-none-any.whl"
    artifact.write_bytes(b"fake wheel")
    runner = FakeSmokeRunner()

    result = module.run_artifact_smoke(tmp_path, artifacts=[artifact], runner=runner)

    assert result.exit_code == 0
    assert result.summary == "artifact smoke passed"
    assert runner.commands[0][:3] == (sys.executable, "-m", "venv")
    install_commands = [
        command
        for command in runner.commands
        if command[1:4] == ("-m", "pip", "install")
    ]
    assert install_commands
    assert "--no-deps" in install_commands[0]
    assert str(artifact) in install_commands[0]
    assert any(
        command[1] == "-c"
        and "importlib.metadata" in command[2]
        and "qa_z.__version__" in command[2]
        and "qa_z.cli:main" in command[2]
        for command in runner.commands
    )


def test_artifact_smoke_fails_without_artifact(tmp_path):
    module = load_smoke_module()
    runner = FakeSmokeRunner()

    result = module.run_artifact_smoke(
        tmp_path,
        artifacts=[tmp_path / "missing.whl"],
        runner=runner,
    )

    assert result.exit_code == 1
    assert result.summary == "artifact smoke failed"
    assert result.checks[0].status == "failed"
    assert "missing artifact" in result.checks[0].detail
    assert runner.commands == []


def test_artifact_smoke_with_deps_runs_onboarding_commands(tmp_path):
    module = load_smoke_module()
    artifact = tmp_path / "qa_z-0.9.8a0-py3-none-any.whl"
    artifact.write_bytes(b"fake wheel")
    runner = FakeSmokeRunner()

    result = module.run_artifact_smoke(
        tmp_path, artifacts=[artifact], runner=runner, with_deps=True
    )

    commands = [" ".join(command) for command in runner.commands]
    assert result.exit_code == 0
    assert any(" qa_z init " in f" {command} " for command in commands)
    assert any("--with-agent-templates" in command for command in commands)
    assert any(" qa_z doctor " in f" {command} " for command in commands)
    assert any(" qa_z plan " in f" {command} " for command in commands)
    assert any(" qa_z review " in f" {command} " for command in commands)


def test_artifact_smoke_cli_can_emit_json(monkeypatch, capsys):
    module = load_smoke_module()

    def fake_run_artifact_smoke(_repo_root, **kwargs):
        assert kwargs["expected_version"] == "0.9.8a0"
        assert kwargs["artifacts"] == [
            Path("dist/custom.whl"),
            Path("dist/custom.tar.gz"),
        ]
        return module.SmokeResult(
            [module.CheckResult("custom_install_smoke", "passed", "ok")]
        )

    monkeypatch.setattr(module, "run_artifact_smoke", fake_run_artifact_smoke)

    exit_code = module.main(
        [
            "--wheel",
            "dist/custom.whl",
            "--sdist",
            "dist/custom.tar.gz",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload == {
        "summary": "artifact smoke passed",
        "exit_code": 0,
        "checks": [
            {
                "name": "custom_install_smoke",
                "status": "passed",
                "detail": "ok",
            }
        ],
    }
