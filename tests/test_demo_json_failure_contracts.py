"""Regression tests for demo JSON failure payloads."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main
import qa_z.commands.demo as demo_module


def test_demo_auth_bug_json_reports_copied_resource_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    copied_readme = tmp_path / ".qa-z" / "demo" / "auth-bug" / "README.md"
    original_write_bytes = Path.write_bytes

    def fail_demo_copy(path: Path, *args: object, **kwargs: object) -> int:
        if path == copied_readme:
            raise OSError("disk full")
        return original_write_bytes(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_bytes", fail_demo_copy)

    exit_code = main(["demo", "auth-bug", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.demo.auth_bug_error",
        "schema_version": 1,
        "error": "artifact_write_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z demo auth-bug: artifact write error:" in output["message"]
    assert "could not prepare demo artifacts" in output["message"]
    assert str(copied_readme) in output["message"]
    assert "disk full" in output["message"]


def test_demo_auth_bug_json_reports_resource_directory_create_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    demo_root = tmp_path / ".qa-z" / "demo" / "auth-bug"
    original_mkdir = Path.mkdir

    def fail_demo_dir(path: Path, *args: object, **kwargs: object) -> None:
        if path == demo_root:
            raise OSError("disk full")
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", fail_demo_dir)

    exit_code = main(["demo", "auth-bug", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["kind"] == "qa_z.demo.auth_bug_error"
    assert output["schema_version"] == 1
    assert output["error"] == "artifact_write_error"
    assert output["exit_code"] == 2
    assert "could not prepare demo artifacts" in output["message"]
    assert str(demo_root) in output["message"]
    assert "disk full" in output["message"]


def test_demo_auth_bug_json_reports_nested_command_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_guard(command: list[str], *, suppress_stdout: bool) -> int:
        assert suppress_stdout is True
        if command[0] == "guard":
            return 7
        return 0

    monkeypatch.setattr(demo_module, "run_demo_subcommand", fail_guard)

    exit_code = main(["demo", "auth-bug", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output == {
        "kind": "qa_z.demo.auth_bug_error",
        "schema_version": 1,
        "error": "demo_run_error",
        "exit_code": 1,
        "message": (
            "qa-z demo auth-bug: failed to create demo evidence "
            "(plan_exit=0, guard_exit=7)"
        ),
    }
