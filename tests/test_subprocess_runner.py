"""Tests for deterministic subprocess check execution."""

from __future__ import annotations

import sys

from qa_z.runners.fast import normalize_check_result
from qa_z.runners.models import CheckResult, CheckSpec
from qa_z.runners.subprocess import TAIL_LIMIT, run_check


def test_run_check_decodes_utf8_output_on_non_utf8_windows_locales(tmp_path) -> None:
    spec = CheckSpec(
        id="utf8_failure",
        command=[
            sys.executable,
            "-c",
            (
                "import sys; "
                "sys.stderr.buffer.write("
                "'\\uc0ac\\uc6a9\\ud560 \\uc218 \\uc5c6\\uc74c\\n'.encode('utf-8')"
                "); "
                "sys.exit(1)"
            ),
        ],
        kind="test",
    )

    result = run_check(spec, cwd=tmp_path)

    assert result.status == "failed"
    assert result.exit_code == 1
    assert "\uc0ac\uc6a9\ud560 \uc218 \uc5c6\uc74c" in result.stderr_tail


def test_run_check_forces_utf8_mode_for_python_subprocess_tools(tmp_path) -> None:
    spec = CheckSpec(
        id="python_utf8_env",
        command=[
            sys.executable,
            "-c",
            (
                "import os, sys; "
                "assert os.environ.get('PYTHONUTF8') == '1'; "
                "assert os.environ.get('PYTHONIOENCODING') == 'utf-8'; "
                "assert sys.flags.utf8_mode == 1"
            ),
        ],
        kind="static-analysis",
    )

    result = run_check(spec, cwd=tmp_path)

    assert result.status == "passed"
    assert result.exit_code == 0


def test_run_check_keeps_full_stdout_for_machine_consumers(tmp_path) -> None:
    full_stdout = "prefix-" + ("x" * (TAIL_LIMIT + 10))
    spec = CheckSpec(
        id="large",
        command=[sys.executable, "-c", f"print({full_stdout!r}, end='')"],
        kind="static-analysis",
    )

    result = run_check(spec, cwd=tmp_path)

    assert result.status == "passed"
    assert result.stdout == full_stdout
    assert result.stdout_tail == full_stdout[-TAIL_LIMIT:]
    assert "stdout" not in result.to_dict()


def test_normalize_check_result_treats_vitest_no_tests_as_warning() -> None:
    result = normalize_check_result(
        CheckResult(
            id="ts_test",
            tool="vitest",
            command=["vitest", "run"],
            kind="test",
            status="failed",
            exit_code=1,
            duration_ms=10,
            stdout_tail="No test files found, exiting with code 1",
        ),
        no_tests_policy="warn",
        fail_on_missing_tool=True,
    )

    assert result.status == "warning"
    assert result.message == "No tests were collected."


def test_normalize_check_result_can_make_vitest_no_tests_strict() -> None:
    result = normalize_check_result(
        CheckResult(
            id="ts_test",
            tool="vitest",
            command=["vitest", "run"],
            kind="test",
            status="failed",
            exit_code=1,
            duration_ms=10,
            stderr_tail="No test files found, exiting with code 1",
        ),
        no_tests_policy="fail",
        fail_on_missing_tool=True,
    )

    assert result.status == "failed"
    assert result.message == "No tests were collected."
