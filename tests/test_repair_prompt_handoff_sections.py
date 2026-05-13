"""Repair-prompt executor handoff section regression tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.cli import main
from tests.repair_prompt_test_support import (
    write_config,
    write_contract,
    write_grouped_deep_summary,
    write_summary,
)


def test_repair_prompt_includes_executor_handoff_sections(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    write_grouped_deep_summary(tmp_path, "2026-04-11T17-38-52Z")

    exit_code = main(["repair-prompt", "--path", str(tmp_path), "--json"])
    packet = json.loads(capsys.readouterr().out)
    prompt = packet["agent_prompt"]

    assert exit_code == 0
    assert "## Affected Files" in prompt
    assert "* `tests/test_cli.py`" in prompt
    assert "* `src/qa_z/runners/fast.py`" in prompt
    assert "* `src/app.py`" in prompt
    assert "src/db.ts" not in prompt
    assert "## Non-Goals" in prompt
    assert "* Do not call Codex, Claude, or any external LLM/API from QA-Z." in prompt
    assert "## Validation Commands" in prompt
    assert "* `ruff format --check .`" in prompt
    assert "* `mypy src tests`" in prompt
    assert "* `python -m qa_z fast`" in prompt
    assert "* `python -m qa_z deep --from-run latest`" in prompt
