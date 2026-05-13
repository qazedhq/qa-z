"""Failure-contract tests for repair-prompt CLI JSON modes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main
from tests.repair_prompt_test_support import write_config, write_contract


def test_repair_prompt_json_failure_reports_machine_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)

    exit_code = main(
        [
            "repair-prompt",
            "--path",
            str(tmp_path),
            "--from-run",
            "latest",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 4
    assert output == {
        "kind": "qa_z.repair_prompt_error",
        "error": "source_not_found",
        "exit_code": 4,
        "message": output["message"],
    }
    assert "qa-z repair-prompt: source not found:" in output["message"]
