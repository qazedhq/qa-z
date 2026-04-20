"""Tests for the alpha release artifact install-smoke helper."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_artifact_smoke.py"


def load_smoke_module():
    spec = importlib.util.spec_from_file_location(
        "alpha_release_artifact_smoke", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeRunner:
    def __init__(self, failing_command_fragment: str = "") -> None:
        self.commands: list[tuple[str, ...]] = []
        self.failing_command_fragment = failing_command_fragment

    def __call__(self, command, _cwd):
        command_tuple = tuple(str(part) for part in command)
        self.commands.append(command_tuple)
        if self.failing_command_fragment and any(
            self.failing_command_fragment in part for part in command_tuple
        ):
            return 1, "", f"{self.failing_command_fragment} failed"
        return 0, "ok\n", ""


def test_artifact_smoke_installs_wheel_without_dependency_resolution(tmp_path):
    module = load_smoke_module()
    artifact = tmp_path / "qa_z-0.9.8a0-py3-none-any.whl"
    artifact.write_bytes(b"fake wheel")
    runner = FakeRunner()

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
    runner = FakeRunner()

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
