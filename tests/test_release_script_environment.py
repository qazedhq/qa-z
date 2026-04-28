from __future__ import annotations

import subprocess

from tests.alpha_release_artifact_smoke_test_support import load_smoke_module
from tests.alpha_release_bundle_manifest_test_support import load_manifest_module
from tests.alpha_release_preflight_test_support import load_preflight_module
from tests.runtime_artifact_cleanup_test_support import load_cleanup_module
from tests.worktree_commit_plan_test_support import load_plan_module


def _assert_runner_uses_safe_env(loader, monkeypatch, tmp_path) -> None:
    module = loader()
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = list(command)
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setenv("TEMP", str(tmp_path / "temp"))
    monkeypatch.delenv("RUFF_CACHE_DIR", raising=False)
    support_module = (
        getattr(module, "_ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT", None)
        or getattr(module, "_ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT", None)
        or module
    )
    monkeypatch.setattr(support_module.subprocess, "run", fake_run)

    exit_code, stdout, stderr = module.subprocess_runner(["git", "status"], tmp_path)

    assert exit_code == 0
    assert stdout == "ok\n"
    assert stderr == ""
    assert captured["cwd"] == tmp_path
    env = captured["env"]
    assert isinstance(env, dict)
    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["RUFF_CACHE_DIR"].endswith("qa-z-ruff-cache")
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"


def test_alpha_release_preflight_subprocess_runner_uses_safe_env(
    monkeypatch, tmp_path
) -> None:
    _assert_runner_uses_safe_env(load_preflight_module, monkeypatch, tmp_path)


def test_alpha_release_artifact_smoke_subprocess_runner_uses_safe_env(
    monkeypatch, tmp_path
) -> None:
    _assert_runner_uses_safe_env(load_smoke_module, monkeypatch, tmp_path)


def test_alpha_release_bundle_manifest_subprocess_runner_uses_safe_env(
    monkeypatch, tmp_path
) -> None:
    _assert_runner_uses_safe_env(load_manifest_module, monkeypatch, tmp_path)


def test_runtime_artifact_cleanup_subprocess_runner_uses_safe_env(
    monkeypatch, tmp_path
) -> None:
    _assert_runner_uses_safe_env(load_cleanup_module, monkeypatch, tmp_path)


def test_worktree_commit_plan_subprocess_runner_uses_safe_env(
    monkeypatch, tmp_path
) -> None:
    _assert_runner_uses_safe_env(load_plan_module, monkeypatch, tmp_path)
