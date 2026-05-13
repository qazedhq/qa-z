"""JSON config-loader failure contracts for CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main


def write_broken_config(tmp_path: Path) -> None:
    (tmp_path / "qa-z.yaml").write_text("project: [\n", encoding="utf-8")


def assert_error_payload(
    output: dict[str, object],
    *,
    kind: str,
    message_prefix: str,
    command: str | None = None,
) -> None:
    expected: dict[str, object] = {
        "kind": kind,
        "error": "configuration_error",
        "exit_code": 2,
        "message": output["message"],
    }
    if command:
        expected["command"] = command

    assert output == expected
    assert isinstance(output["message"], str)
    assert output["message"].startswith(message_prefix)


def test_repair_prompt_json_reports_broken_config_as_machine_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_broken_config(tmp_path)

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert_error_payload(
        output,
        kind="qa_z.repair_prompt_error",
        message_prefix="qa-z repair-prompt: configuration error:",
    )


def test_repair_prompt_handoff_json_reports_broken_config_as_machine_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_broken_config(tmp_path)

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--handoff-json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert_error_payload(
        output,
        kind="qa_z.repair_prompt_error",
        message_prefix="qa-z repair-prompt: configuration error:",
    )


def test_executor_result_ingest_json_reports_broken_config_as_machine_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_broken_config(tmp_path)
    result_path = tmp_path / "executor-result.json"
    result_path.write_text("{}", encoding="utf-8")

    exit_code = main(
        [
            "executor-result",
            "ingest",
            "--path",
            str(tmp_path),
            "--result",
            str(result_path),
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert_error_payload(
        output,
        kind="qa_z.executor_result_error",
        command="ingest",
        message_prefix="qa-z executor-result ingest: configuration error:",
    )


def test_autonomy_json_reports_broken_config_as_machine_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_broken_config(tmp_path)

    exit_code = main(["autonomy", "--path", str(tmp_path), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert_error_payload(
        output,
        kind="qa_z.autonomy_error",
        message_prefix="qa-z autonomy: configuration error:",
    )
