"""Tests for git runtime signal inputs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import qa_z.git_runtime as git_runtime_module


def test_git_stdout_runs_git_with_utf8_and_returns_text(
    tmp_path: Path, monkeypatch
) -> None:
    recorded: dict[str, Any] = {}

    def fake_run(command, **kwargs):
        recorded["command"] = command
        recorded["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            command, 0, stdout="feature/demo\n", stderr=""
        )

    monkeypatch.setattr("qa_z.git_runtime.subprocess.run", fake_run)

    output = git_runtime_module.git_stdout(
        tmp_path, ["rev-parse", "--abbrev-ref", "HEAD"]
    )

    assert output == "feature/demo"
    assert recorded["command"] == ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    assert recorded["kwargs"]["cwd"] == tmp_path
    assert recorded["kwargs"]["text"] is True
    assert recorded["kwargs"]["encoding"] == "utf-8"
    assert recorded["kwargs"]["errors"] == "replace"
    assert recorded["kwargs"]["check"] is False
    assert recorded["kwargs"]["env"]["PYTHONUTF8"] == "1"
    assert recorded["kwargs"]["env"]["PYTHONIOENCODING"] == "utf-8"


def test_git_stdout_returns_none_for_git_failures(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "qa_z.git_runtime.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 128, stdout="", stderr="fatal: not a git repository"
        ),
    )

    assert git_runtime_module.git_stdout(tmp_path, ["rev-parse", "HEAD"]) is None


def test_git_stdout_returns_none_when_git_invocation_raises_oserror(
    tmp_path: Path, monkeypatch
) -> None:
    def fake_run(command, **kwargs):
        raise OSError("git missing")

    monkeypatch.setattr("qa_z.git_runtime.subprocess.run", fake_run)

    assert git_runtime_module.git_stdout(tmp_path, ["status", "--short"]) is None
