"""Tests for deterministic subprocess check execution."""

from __future__ import annotations

import sys

import qa_z.runners.subprocess as subprocess_runner
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


def test_run_check_rejects_blank_executable(tmp_path) -> None:
    spec = CheckSpec(
        id="blank_executable",
        command=[""],
        kind="test",
    )

    result = run_check(spec, cwd=tmp_path)

    assert result.status == "error"
    assert result.exit_code is None
    assert result.error_type == "invalid_command"
    assert "empty" in result.message


def test_run_check_normalizes_invalid_working_directory(tmp_path) -> None:
    spec = CheckSpec(
        id="invalid_cwd",
        command=[sys.executable, "-c", "print('unreachable')"],
        kind="test",
    )

    result = run_check(spec, cwd=tmp_path / "missing-workspace")

    assert result.status == "error"
    assert result.exit_code is None
    assert result.error_type == "invalid_cwd"
    assert "working directory" in result.message
    assert str(tmp_path / "missing-workspace") in result.stderr_tail


def test_run_check_normalizes_subprocess_os_error(tmp_path, monkeypatch) -> None:
    def raise_permission_error(*_args, **_kwargs):
        raise PermissionError("permission denied by OS")

    monkeypatch.setattr(subprocess_runner.subprocess, "run", raise_permission_error)
    spec = CheckSpec(
        id="os_error",
        command=[sys.executable, "-c", "print('unreachable')"],
        kind="test",
    )

    result = run_check(spec, cwd=tmp_path)

    assert result.status == "error"
    assert result.exit_code is None
    assert result.error_type == "execution_error"
    assert result.message == f"Could not execute check command: {sys.executable}"
    assert "permission denied by OS" in result.stderr_tail


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


def test_check_result_serialization_redacts_secret_like_output() -> None:
    result = CheckResult(
        id="secret_probe",
        tool="python",
        command=["python", "--token=raw-token-value"],
        kind="test",
        status="failed",
        exit_code=1,
        duration_ms=1,
        stdout="TOKEN=raw-token-value",
        stdout_tail="TOKEN=raw-token-value\nAuthorization: Bearer abc.def.ghi",
        stderr_tail="password: hunter2",
        message="api_key=abcdef",
        grouped_findings=[
            {
                "rule_id": "custom.secret",
                "severity": "ERROR",
                "path": "src/app.py",
                "count": 1,
                "representative_line": 3,
                "message": "password=hunter2",
            }
        ],
        findings=[
            {
                "rule_id": "custom.secret",
                "severity": "ERROR",
                "path": "src/app.py",
                "line": 3,
                "message": "api_key=abcdef",
            }
        ],
        findings_count=1,
        blocking_findings_count=1,
        filtered_findings_count=0,
    )

    payload = result.to_dict()

    assert result.stdout == "TOKEN=raw-token-value"
    assert "raw-token-value" not in payload["command"]
    assert "[REDACTED_TOKEN]" in payload["command"][1]
    assert "raw-token-value" not in payload["stdout_tail"]
    assert "abc.def.ghi" not in payload["stdout_tail"]
    assert "hunter2" not in payload["stderr_tail"]
    assert "abcdef" not in payload["message"]
    assert "hunter2" not in payload["grouped_findings"][0]["message"]
    assert "abcdef" not in payload["findings"][0]["message"]
    assert "[REDACTED_TOKEN]" in payload["stdout_tail"]
    assert "[REDACTED_SECRET]" in payload["stderr_tail"]


def test_check_result_serialization_redacts_url_userinfo_credentials() -> None:
    result = CheckResult(
        id="url_secret_probe",
        tool="git",
        command=[
            "git",
            "clone",
            "https://git-user:url-token@example.test/private.git",
        ],
        kind="test",
        status="failed",
        exit_code=1,
        duration_ms=1,
        stdout_tail="fetch https://git-user:url-token@example.test/private.git",
        stderr_tail="remote https://another-user:another-token@example.test/repo.git",
        message="Dependency URL https://third-user:third-token@example.test/pkg",
    )

    payload = result.to_dict()
    rendered = str(payload)

    for raw_secret in (
        "git-user",
        "url-token",
        "another-user",
        "another-token",
        "third-user",
        "third-token",
    ):
        assert raw_secret not in rendered
    assert "https://[REDACTED_SECRET]@example.test/private.git" in payload["command"]
    assert (
        payload["stdout_tail"]
        == "fetch https://[REDACTED_SECRET]@example.test/private.git"
    )
    assert (
        payload["stderr_tail"]
        == "remote https://[REDACTED_SECRET]@example.test/repo.git"
    )


def test_check_serialization_redacts_split_secret_args_and_auth_headers() -> None:
    command = [
        "custom-tool",
        "--token",
        "raw-token-value",
        "--client-secret",
        "raw-client-secret",
    ]
    spec = CheckSpec(id="split_secret_probe", command=command, kind="test")
    result = CheckResult(
        id="split_secret_probe",
        tool="custom-tool",
        command=command,
        kind="test",
        status="failed",
        exit_code=1,
        duration_ms=1,
        stdout_tail="Authorization: Basic raw-basic-credential",
        stderr_tail="authorization: Digest raw-digest-credential, next=value",
    )

    spec_payload = spec.to_dict()
    result_payload = result.to_dict()
    rendered = str({"spec": spec_payload, "result": result_payload})

    for raw_secret in (
        "raw-token-value",
        "raw-client-secret",
        "raw-basic-credential",
        "raw-digest-credential",
    ):
        assert raw_secret not in rendered
    assert spec_payload["command"][2] == "[REDACTED_TOKEN]"
    assert spec_payload["command"][4] == "[REDACTED_SECRET]"
    assert result_payload["command"][2] == "[REDACTED_TOKEN]"
    assert result_payload["command"][4] == "[REDACTED_SECRET]"
    assert result_payload["stdout_tail"] == "Authorization: [REDACTED_TOKEN]"
    assert "authorization: [REDACTED_TOKEN]" in result_payload["stderr_tail"]


def test_check_result_serialization_redacts_prefixed_env_secret_names() -> None:
    result = CheckResult(
        id="prefixed_secret_probe",
        tool="python",
        command=[
            "python",
            "--github-token=github-raw",
            "OPENAI_API_KEY=openai-raw",
        ],
        kind="test",
        status="failed",
        exit_code=1,
        duration_ms=1,
        stdout_tail=(
            "GITHUB_TOKEN=github-raw\n"
            "OPENAI_API_KEY=openai-raw\n"
            "ANTHROPIC_API_KEY=anthropic-raw"
        ),
        stderr_tail=("AWS_SECRET_ACCESS_KEY=aws-raw\nCLIENT_SECRET=client-raw"),
    )

    payload = result.to_dict()
    rendered = str(payload)

    for raw_secret in (
        "github-raw",
        "openai-raw",
        "anthropic-raw",
        "aws-raw",
        "client-raw",
    ):
        assert raw_secret not in rendered
    assert "GITHUB_TOKEN=[REDACTED_TOKEN]" in payload["stdout_tail"]
    assert "--github-token=[REDACTED_TOKEN]" in payload["command"][1]
    assert "OPENAI_API_KEY=[REDACTED_SECRET]" in payload["stdout_tail"]
    assert "AWS_SECRET_ACCESS_KEY=[REDACTED_SECRET]" in payload["stderr_tail"]
    assert "CLIENT_SECRET=[REDACTED_SECRET]" in payload["stderr_tail"]


def test_check_result_serialization_redacts_json_shaped_secret_output() -> None:
    result = CheckResult(
        id="json_secret_probe",
        tool="custom-tool",
        command=["custom-tool"],
        kind="static-analysis",
        status="failed",
        exit_code=1,
        duration_ms=1,
        stdout_tail='{"GITHUB_TOKEN":"github-json"}',
        stderr_tail='{"OPENAI_API_KEY": "openai-json"}',
        message='{"CLIENT_SECRET":"client-json"}',
        grouped_findings=[
            {
                "rule_id": "custom.secret",
                "severity": "ERROR",
                "path": "src/app.py",
                "count": 1,
                "representative_line": 3,
                "message": '{"password":"password-json"}',
            }
        ],
        findings=[
            {
                "rule_id": "custom.secret",
                "severity": "ERROR",
                "path": "src/app.py",
                "line": 3,
                "message": '{"AWS_SECRET_ACCESS_KEY":"aws-json"}',
            }
        ],
        scan_warning_count=1,
        scan_warnings=[{"message": '{"GITHUB_TOKEN":"scan-json"}', "token_count": 3}],
        findings_count=1,
        blocking_findings_count=1,
        filtered_findings_count=0,
    )

    payload = result.to_dict()
    rendered = str(payload)

    for raw_secret in (
        "github-json",
        "openai-json",
        "client-json",
        "password-json",
        "aws-json",
        "scan-json",
    ):
        assert raw_secret not in rendered
    assert "[REDACTED_TOKEN]" in rendered
    assert "[REDACTED_SECRET]" in rendered
    assert payload["scan_warnings"][0]["token_count"] == 3


def test_check_result_serialization_redacts_secret_like_mapping_keys() -> None:
    result = CheckResult(
        id="structured_secret_probe",
        tool="semgrep",
        command=["semgrep", "--json"],
        kind="static-analysis",
        status="passed",
        exit_code=0,
        duration_ms=1,
        scan_warning_count=1,
        scan_warnings=[
            {
                "path": "src/app.py",
                "AWS_SECRET_ACCESS_KEY": "aws-raw",
                "token_count": 3,
            }
        ],
        policy={
            "OPENAI_API_KEY": "openai-raw",
            "nested": {"CLIENT_SECRET": "client-raw"},
            "token_count": 3,
        },
    )

    payload = result.to_dict()
    rendered = str(payload)

    for raw_secret in ("aws-raw", "openai-raw", "client-raw"):
        assert raw_secret not in rendered
    assert payload["scan_warnings"][0]["AWS_SECRET_ACCESS_KEY"] == "[REDACTED_SECRET]"
    assert payload["scan_warnings"][0]["token_count"] == 3
    assert payload["policy"]["OPENAI_API_KEY"] == "[REDACTED_SECRET]"
    assert payload["policy"]["nested"]["CLIENT_SECRET"] == "[REDACTED_SECRET]"
    assert payload["policy"]["token_count"] == 3


def test_check_result_serialization_redacts_secret_key_suffixes() -> None:
    result = CheckResult(
        id="structured_secret_suffix_probe",
        tool="semgrep",
        command=["semgrep", "--json"],
        kind="static-analysis",
        status="passed",
        exit_code=0,
        duration_ms=1,
        message='{"GITHUB_TOKEN_VALUE":"github-json"}',
        scan_warning_count=1,
        scan_warnings=[
            {
                "path": "src/app.py",
                "GITHUB_TOKEN_VALUE": "github-raw",
                "token_count": 3,
            }
        ],
        policy={
            "OPENAI_API_KEY_RAW": "openai-raw",
            "nested": {"CLIENT_SECRET_VALUE": "client-raw"},
            "token_count": 3,
        },
    )

    payload = result.to_dict()
    rendered = str(payload)

    for raw_secret in ("github-json", "github-raw", "openai-raw", "client-raw"):
        assert raw_secret not in rendered
    assert payload["scan_warnings"][0]["GITHUB_TOKEN_VALUE"] == "[REDACTED_TOKEN]"
    assert payload["scan_warnings"][0]["token_count"] == 3
    assert payload["policy"]["OPENAI_API_KEY_RAW"] == "[REDACTED_SECRET]"
    assert payload["policy"]["nested"]["CLIENT_SECRET_VALUE"] == "[REDACTED_SECRET]"
    assert payload["policy"]["token_count"] == 3


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
