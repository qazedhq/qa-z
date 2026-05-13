"""Failure-contract tests for repair-prompt CLI JSON modes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main
from tests.repair_prompt_test_support import write_config, write_contract, write_summary


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


def test_repair_prompt_json_reports_artifact_write_failure(
    monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    blocked_path = (
        tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z" / "repair" / "codex.md"
    )
    original_write_text = Path.write_text

    def fail_codex_handoff(path, *args, **kwargs):
        if path == blocked_path:
            raise OSError("disk full")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_codex_handoff)

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

    assert exit_code == 2
    assert output["kind"] == "qa_z.repair_prompt_error"
    assert output["error"] == "artifact_write_error"
    assert "qa-z repair-prompt: artifact write error:" in output["message"]
    assert "could not write repair-prompt codex handoff" in output["message"]
    assert str(blocked_path) in output["message"]
    assert "disk full" in output["message"]


def test_repair_prompt_json_reports_prompt_artifact_write_failure(
    monkeypatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    blocked_path = (
        tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z" / "repair" / "prompt.md"
    )
    original_write_text = Path.write_text

    def fail_prompt_artifact(path, *args, **kwargs):
        if path == blocked_path:
            raise OSError("disk full")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_prompt_artifact)

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

    assert exit_code == 2
    assert output["kind"] == "qa_z.repair_prompt_error"
    assert output["error"] == "artifact_write_error"
    assert "qa-z repair-prompt: artifact write error:" in output["message"]
    assert "could not write repair-prompt artifact" in output["message"]
    assert str(blocked_path) in output["message"]
    assert "disk full" in output["message"]
