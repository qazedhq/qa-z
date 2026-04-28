from __future__ import annotations

import subprocess

from tests.alpha_release_gate_test_support import load_gate_module


def test_alpha_release_gate_subprocess_runner_uses_safe_tool_env(
    monkeypatch, tmp_path
) -> None:
    module = load_gate_module()
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = list(command)
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setenv("TEMP", str(tmp_path / "temp"))
    monkeypatch.delenv("RUFF_CACHE_DIR", raising=False)
    monkeypatch.setattr(module.subprocess, "run", fake_run)

    exit_code, stdout, stderr = module.subprocess_runner(
        ["python", "-m", "ruff"], tmp_path
    )

    assert exit_code == 0
    assert stdout == "ok\n"
    assert stderr == ""
    assert captured["cwd"] == tmp_path
    env = captured["env"]
    assert isinstance(env, dict)
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["RUFF_CACHE_DIR"].endswith("qa-z-ruff-cache")
