from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from qa_z.subprocess_env import build_tool_subprocess_env


ROOT = Path(__file__).resolve().parents[1]


def _run_python(source: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", source],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _run_command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args),
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_pytest_cli_can_collect_test_support_modules() -> None:
    completed = _run_command("pytest", "-q", "tests/test_verification_test_support.py")

    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_pytest_cli_can_collect_alpha_release_support_modules() -> None:
    completed = _run_command(
        "pytest", "-q", "tests/test_alpha_release_artifact_smoke.py"
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_mypy_can_scan_src_and_tests_together() -> None:
    completed = _run_command("mypy", "src", "tests")

    assert completed.returncode == 0, completed.stderr or completed.stdout


def test_mypy_ini_pins_cache_under_temp() -> None:
    mypy_ini = (ROOT / "mypy.ini").read_text(encoding="utf-8")

    assert "[mypy]" in mypy_ini
    assert "cache_dir = $TEMP/qa-z-mypy-cache" in mypy_ini


def test_pyproject_pins_ruff_cache_to_safe_local_directory() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "[tool.ruff]" in pyproject
    assert 'cache-dir = "~/AppData/Local/Temp/qa-z-ruff-cache"' in pyproject


def test_tool_subprocess_env_sets_utf8_and_safe_ruff_cache() -> None:
    env = build_tool_subprocess_env({"TEMP": r"F:\Temp"})

    assert env["PYTHONUTF8"] == "1"
    assert env["PYTHONIOENCODING"] == "utf-8"
    assert env["RUFF_CACHE_DIR"] == r"F:\Temp\qa-z-ruff-cache"


def test_tool_subprocess_env_preserves_posix_temp_path_style() -> None:
    env = build_tool_subprocess_env({"TEMP": "/tmp"})

    assert env["RUFF_CACHE_DIR"] == "/tmp/qa-z-ruff-cache"


def test_tool_subprocess_env_preserves_explicit_ruff_cache_dir() -> None:
    env = build_tool_subprocess_env(
        {
            "TEMP": r"F:\Temp",
            "RUFF_CACHE_DIR": r"F:\Already\Chosen",
        }
    )

    assert env["RUFF_CACHE_DIR"] == r"F:\Already\Chosen"


def test_ruff_cli_can_run_without_cache_access_warning() -> None:
    completed = _run_command(
        sys.executable,
        "-m",
        "ruff",
        "check",
        "tests/test_fast_gate_environment.py",
    )

    combined_output = f"{completed.stdout}\n{completed.stderr}".lower()
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "os error 5" not in combined_output
    assert "access is denied" not in combined_output


def test_python_import_can_resolve_tests_namespace_support_modules() -> None:
    completed = _run_python(
        "import tests.verification_test_support; "
        "import tests.worktree_commit_plan_test_support; "
        "import tests.alpha_release_artifact_smoke_test_support; "
        "import tests.alpha_release_bundle_manifest_test_support"
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
