from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "installed_package_smoke.py"


def load_smoke_module():
    cached = sys.modules.get("installed_package_smoke")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "installed_package_smoke", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRunner:
    def __init__(self, *, failing_ids: set[str] | None = None) -> None:
        self.failing_ids = failing_ids or set()
        self.commands: list[tuple[str, ...]] = []

    def __call__(
        self,
        command: Sequence[str],
        _cwd: Path,
        *,
        check_id: str,
        allowed_exit_codes: set[int],
    ) -> tuple[int, str, str]:
        del allowed_exit_codes
        command_tuple = tuple(str(part) for part in command)
        self.commands.append(command_tuple)
        if check_id in self.failing_ids:
            return 9, "", f"{check_id} failed"
        if check_id.endswith("verify"):
            return 1, '{"kind": "qa_z.verify_compare", "verdict": "unchanged"}', ""
        return 0, "ok", ""


def fake_create_venv(path: Path) -> None:
    (path / "Scripts").mkdir(parents=True)


def write_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    wheel = artifacts / "qa_z-0.10.0b0-py3-none-any.whl"
    sdist = artifacts / "qa_z-0.10.0b0.tar.gz"
    wheel.write_bytes(b"wheel")
    sdist.write_bytes(b"sdist")
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


def test_wheel_and_sdist_matrix_runs_installed_runtime_commands(
    tmp_path: Path,
) -> None:
    module = load_smoke_module()
    wheel, sdist = write_artifacts(tmp_path)
    runner = FakeRunner()

    result = module.run_installed_package_smoke(
        tmp_path,
        artifacts=module.PackageArtifacts(wheel=wheel, sdist=sdist),
        runner=runner,
        create_venv=fake_create_venv,
        work_root=tmp_path / "work",
    )
    payload = module.result_payload(tmp_path, result)

    assert payload["summary"] == "installed package smoke passed"
    assert payload["exit_code"] == 0
    assert payload["registry_upload_executed"] is False
    assert payload["artifacts"] == {
        "wheel": "artifacts/qa_z-0.10.0b0-py3-none-any.whl",
        "sdist": "artifacts/qa_z-0.10.0b0.tar.gz",
    }
    assert {check["artifact_kind"] for check in payload["checks"]} == {
        "wheel",
        "sdist",
    }
    commands = "\n".join(payload_commands(payload))
    for expected in (
        "pip install",
        "qa-z --help",
        "python.exe -m qa_z --help",
        "qa-z doctor --json",
        "qa-z demo auth-bug --json",
        "qa-z guard --from-run latest --adapter codex",
        "qa-z repair-prompt --from-run latest --adapter codex",
        "qa-z verify --baseline-run latest --candidate-run latest --json",
    ):
        assert expected in commands


def test_verify_exit_one_is_expected_for_unchanged_demo_comparison(
    tmp_path: Path,
) -> None:
    module = load_smoke_module()
    wheel, sdist = write_artifacts(tmp_path)
    runner = FakeRunner()

    result = module.run_installed_package_smoke(
        tmp_path,
        artifacts=module.PackageArtifacts(wheel=wheel, sdist=sdist),
        runner=runner,
        create_venv=fake_create_venv,
        work_root=tmp_path / "work",
    )

    verify_checks = [check for check in result.checks if check.id.endswith("verify")]
    assert verify_checks
    assert {check.status for check in verify_checks} == {"PASS"}
    assert {check.exit_code for check in verify_checks} == {1}
    assert all("expected exit code" in check.reason for check in verify_checks)


def test_failures_are_reported_without_upload_or_release_commands(
    tmp_path: Path,
) -> None:
    module = load_smoke_module()
    wheel, sdist = write_artifacts(tmp_path)
    runner = FakeRunner(failing_ids={"wheel_guard"})

    result = module.run_installed_package_smoke(
        tmp_path,
        artifacts=module.PackageArtifacts(wheel=wheel, sdist=sdist),
        runner=runner,
        create_venv=fake_create_venv,
        work_root=tmp_path / "work",
    )
    payload = module.result_payload(tmp_path, result)
    command_blob = "\n".join(payload_commands(payload)).lower()

    assert payload["summary"] == "installed package smoke failed"
    assert payload["exit_code"] == 1
    assert payload["registry_upload_executed"] is False
    assert "upload" not in command_blob
    assert "publish" not in command_blob
    assert "git tag" not in command_blob
    assert "release create" not in command_blob
    assert "deploy" not in command_blob
