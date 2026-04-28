"""Behavior tests for repair-prompt contract and ordering details."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from qa_z.cli import main
from qa_z.reporters.repair_prompt import extract_candidate_files
from tests.repair_prompt_test_support import write_config, write_contract, write_summary


def test_repair_prompt_contract_parsing_prefers_front_matter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Front matter title")
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["contract"]["title"] == "Front matter title"
    assert packet["contract"]["scope_items"] == [
        "token refresh path",
        "expired token handling",
    ]
    assert "fallback scope" not in packet["contract"]["scope_items"]


def test_repair_prompt_contract_parsing_falls_back_to_markdown(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path, title="Markdown fallback title", front_matter=False)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["contract"]["title"] == "Markdown fallback title"
    assert packet["contract"]["summary"] == "Markdown fallback summary."


def test_suggested_fix_order_is_stable(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(
        tmp_path,
        "2026-04-11T17-38-52Z",
        checks=[
            {
                "id": "py_test",
                "tool": "pytest",
                "command": ["pytest", "-q"],
                "kind": "test",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
            },
            {
                "id": "py_type",
                "tool": "mypy",
                "command": ["mypy", "src", "tests"],
                "kind": "typecheck",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
            },
            {
                "id": "py_lint",
                "tool": "ruff",
                "command": ["ruff", "check", "."],
                "kind": "lint",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
            },
            {
                "id": "py_format",
                "tool": "ruff",
                "command": ["ruff", "format", "--check", "."],
                "kind": "format",
                "status": "failed",
                "exit_code": 1,
                "duration_ms": 55,
                "stdout_tail": "",
                "stderr_tail": "",
            },
        ],
    )

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert packet["suggested_fix_order"] == [
        "py_format",
        "py_lint",
        "py_type",
        "py_test",
    ]


def test_candidate_files_extracted_from_failure_output() -> None:
    text = dedent(
        """
        tests/test_cli.py:10: assertion failed
        src\\qa_z\\runners\\fast.py:20: error
        ignored.txt
        app/components/Login.tsx(12,2): error
        """
    )

    assert extract_candidate_files(text) == [
        "tests/test_cli.py",
        "src/qa_z/runners/fast.py",
        "app/components/Login.tsx",
    ]
