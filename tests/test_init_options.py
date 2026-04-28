"""Tests for optional qa-z init outputs."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from qa_z.cli import main


def load_initialized_config(root: Path) -> dict[str, object]:
    return yaml.safe_load((root / "qa-z.yaml").read_text(encoding="utf-8"))


def test_init_with_agent_templates_creates_agents_and_claude_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path), "--with-agent-templates"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "CLAUDE.md").is_file()
    assert "created: AGENTS.md" in output
    assert "created: CLAUDE.md" in output


def test_init_with_profile_python_limits_config_to_python_checks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path), "--profile", "python"])
    capsys.readouterr()
    config = load_initialized_config(tmp_path)

    assert exit_code == 0
    assert config["project"]["languages"] == ["python"]  # type: ignore[index]
    assert [
        check["id"]
        for check in config["fast"]["checks"]  # type: ignore[index]
    ] == ["py_lint", "py_format", "py_type", "py_test"]


def test_init_with_profile_typescript_limits_config_to_typescript_checks(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path), "--profile", "typescript"])
    capsys.readouterr()
    config = load_initialized_config(tmp_path)

    assert exit_code == 0
    assert config["project"]["languages"] == ["typescript"]  # type: ignore[index]
    assert [
        check["id"]
        for check in config["fast"]["checks"]  # type: ignore[index]
    ] == ["ts_lint", "ts_type", "ts_test"]


def test_init_with_profile_monorepo_uses_smart_selection(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path), "--profile", "monorepo"])
    capsys.readouterr()
    config = load_initialized_config(tmp_path)

    assert exit_code == 0
    assert config["project"]["languages"] == ["python", "typescript"]  # type: ignore[index]
    assert config["fast"]["selection"]["default_mode"] == "smart"  # type: ignore[index]


def test_init_with_github_workflow_creates_workflow(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path), "--with-github-workflow"])
    output = capsys.readouterr().out

    workflow = tmp_path / ".github" / "workflows" / "qa-z.yml"
    assert exit_code == 0
    assert workflow.is_file()
    assert "python -m qa_z fast" in workflow.read_text(encoding="utf-8")
    assert "created: .github/workflows/qa-z.yml" in output


def test_init_options_are_idempotent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first_exit = main(
        [
            "init",
            "--path",
            str(tmp_path),
            "--with-agent-templates",
            "--with-github-workflow",
        ]
    )
    capsys.readouterr()
    second_exit = main(
        [
            "init",
            "--path",
            str(tmp_path),
            "--with-agent-templates",
            "--with-github-workflow",
        ]
    )
    output = capsys.readouterr().out

    assert first_exit == 0
    assert second_exit == 0
    assert "skipped: AGENTS.md" in output
    assert "skipped: CLAUDE.md" in output
    assert "skipped: .github/workflows/qa-z.yml" in output
