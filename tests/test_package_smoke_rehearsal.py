from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Sequence

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "package_smoke_rehearsal.py"


def load_rehearsal_module():
    cached = sys.modules.get("package_smoke_rehearsal")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "package_smoke_rehearsal", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRunner:
    def __init__(
        self,
        *,
        available_tools: set[str] | None = None,
        failing_tools: set[str] | None = None,
    ) -> None:
        self.available_tools = available_tools or set()
        self.failing_tools = failing_tools or set()
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command: Sequence[str], _cwd: Path) -> tuple[int, str, str]:
        command_tuple = tuple(str(part) for part in command)
        self.commands.append(command_tuple)
        tool = self._tool_for(command_tuple)
        if self._is_availability_probe(command_tuple):
            if tool in self.available_tools:
                return 0, f"{tool} version\n", ""
            return 1, "", f"{tool} missing"
        if tool in self.failing_tools:
            return 7, "", f"{tool} smoke failed"
        return 0, "ok\n", ""

    @staticmethod
    def _tool_for(command: tuple[str, ...]) -> str:
        if len(command) >= 3 and command[1:3] == ("-m", "twine"):
            return "twine"
        if command and command[0] == "pipx":
            return "pipx"
        if command and command[0] == "uvx":
            return "uvx"
        return "unknown"

    @staticmethod
    def _is_availability_probe(command: tuple[str, ...]) -> bool:
        return command[-1:] == ("--version",)


def write_dist(tmp_path: Path) -> tuple[Path, Path]:
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / "qa_z-0.9.8a0-py3-none-any.whl"
    sdist = dist / "qa_z-0.9.8a0.tar.gz"
    wheel.write_bytes(b"fake wheel")
    sdist.write_bytes(b"fake sdist")
    return wheel, sdist


def payload_commands(payload: dict[str, object]) -> list[str]:
    checks = payload["checks"]
    assert isinstance(checks, list)
    commands: list[str] = []
    for check in checks:
        assert isinstance(check, dict)
        command = check["command"]
        assert isinstance(command, list)
        commands.append(" ".join(str(part) for part in command))
    return commands


def test_missing_tools_are_not_run_and_can_be_allowed(tmp_path: Path) -> None:
    module = load_rehearsal_module()
    write_dist(tmp_path)
    runner = FakeRunner()

    result = module.run_package_smoke_rehearsal(
        tmp_path,
        allow_missing_tools=True,
        runner=runner,
    )
    payload = module.result_payload(tmp_path, result)

    assert payload["exit_code"] == 0
    assert payload["summary"] == "package smoke rehearsal incomplete"
    assert payload["registry_upload_executed"] is False
    assert [check["status"] for check in payload["checks"]] == [
        "NOT RUN",
        "NOT RUN",
        "NOT RUN",
    ]
    assert all("tool unavailable" in check["reason"] for check in payload["checks"])


def test_missing_tools_fail_without_allow_missing_tools(tmp_path: Path) -> None:
    module = load_rehearsal_module()
    write_dist(tmp_path)
    runner = FakeRunner()

    result = module.run_package_smoke_rehearsal(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert result.summary == "package smoke rehearsal incomplete"


def test_subprocess_runner_reports_missing_executable(
    monkeypatch, tmp_path: Path
) -> None:
    module = load_rehearsal_module()

    def fake_run(*_args, **_kwargs):
        raise FileNotFoundError("missing pipx")

    monkeypatch.setattr(
        module._PACKAGE_SMOKE_REHEARSAL_SUPPORT.subprocess, "run", fake_run
    )

    exit_code, stdout, stderr = module.subprocess_runner(
        ["pipx", "--version"], tmp_path
    )

    assert exit_code == 127
    assert stdout == ""
    assert "missing pipx" in stderr


def test_available_tools_pass_and_use_exact_artifact_paths(tmp_path: Path) -> None:
    module = load_rehearsal_module()
    write_dist(tmp_path)
    runner = FakeRunner(available_tools={"twine", "pipx", "uvx"})

    result = module.run_package_smoke_rehearsal(tmp_path, runner=runner)
    payload = module.result_payload(tmp_path, result)

    assert payload["exit_code"] == 0
    assert payload["wheel"] == "dist/qa_z-0.9.8a0-py3-none-any.whl"
    assert payload["sdist_paths"] == ["dist/qa_z-0.9.8a0.tar.gz"]
    assert [check["status"] for check in payload["checks"]] == [
        "PASS",
        "PASS",
        "PASS",
    ]
    commands = payload_commands(payload)
    assert any(
        " -m twine check dist/qa_z-0.9.8a0-py3-none-any.whl "
        "dist/qa_z-0.9.8a0.tar.gz" in command
        for command in commands
    )
    assert "pipx run --spec dist/qa_z-0.9.8a0-py3-none-any.whl qa-z --help" in commands
    assert "uvx --from dist/qa_z-0.9.8a0-py3-none-any.whl qa-z --help" in commands


def test_available_tool_failure_is_a_failed_check(tmp_path: Path) -> None:
    module = load_rehearsal_module()
    write_dist(tmp_path)
    runner = FakeRunner(
        available_tools={"twine", "pipx", "uvx"},
        failing_tools={"pipx"},
    )

    result = module.run_package_smoke_rehearsal(tmp_path, runner=runner)
    payload = module.result_payload(tmp_path, result)
    checks = {check["id"]: check for check in payload["checks"]}

    assert payload["exit_code"] == 1
    assert checks["pipx_wheel_help"]["status"] == "FAIL"
    assert checks["pipx_wheel_help"]["exit_code"] == 7
    assert "pipx smoke failed" in checks["pipx_wheel_help"]["reason"]


def test_multiple_wheels_fail_unless_exact_wheel_is_provided(tmp_path: Path) -> None:
    module = load_rehearsal_module()
    selected_wheel, _sdist = write_dist(tmp_path)
    extra_wheel = tmp_path / "dist" / "qa_z-0.9.9-py3-none-any.whl"
    extra_wheel.write_bytes(b"extra wheel")
    runner = FakeRunner(available_tools={"twine", "pipx", "uvx"})

    with pytest.raises(module.RehearsalError, match="multiple wheel artifacts"):
        module.run_package_smoke_rehearsal(tmp_path, runner=runner)

    result = module.run_package_smoke_rehearsal(
        tmp_path,
        wheel=str(selected_wheel),
        runner=runner,
    )

    assert result.wheel == selected_wheel
    assert result.exit_code == 0


def test_executable_commands_never_include_upload_tag_release_or_deploy(
    tmp_path: Path,
) -> None:
    module = load_rehearsal_module()
    write_dist(tmp_path)
    runner = FakeRunner(available_tools={"twine", "pipx", "uvx"})

    result = module.run_package_smoke_rehearsal(tmp_path, runner=runner)
    payload = module.result_payload(tmp_path, result)
    command_blob = "\n".join(payload_commands(payload)).lower()

    assert payload["registry_upload_executed"] is False
    assert "upload" not in command_blob
    assert "publish" not in command_blob
    assert "git tag" not in command_blob
    assert "release create" not in command_blob
    assert "deploy" not in command_blob
    assert "twine check" in command_blob
