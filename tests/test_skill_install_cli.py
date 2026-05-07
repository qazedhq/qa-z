"""CLI tests for installing QA-Z merge-safety instructions."""

from __future__ import annotations

from pathlib import Path

from qa_z.cli import main


def test_skill_install_codex_writes_agents_file(tmp_path: Path, capsys) -> None:
    exit_code = main(["skill", "install", "codex", "--path", str(tmp_path)])
    output = capsys.readouterr().out
    agents = tmp_path / "AGENTS.md"

    assert exit_code == 0
    assert "installed codex: AGENTS.md" in output
    assert agents.exists()
    assert "QA-Z Merge Safety" in agents.read_text(encoding="utf-8")
    assert b"\r\n" not in agents.read_bytes()


def test_skill_install_refuses_overwrite_by_default(tmp_path: Path, capsys) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Existing\n", encoding="utf-8")

    exit_code = main(["skill", "install", "codex", "--path", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "refusing to overwrite: AGENTS.md" in output
    assert agents.read_text(encoding="utf-8") == "# Existing\n"


def test_skill_install_force_overwrites_existing_file(tmp_path: Path, capsys) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Existing\n", encoding="utf-8")

    exit_code = main(["skill", "install", "codex", "--path", str(tmp_path), "--force"])
    capsys.readouterr()

    assert exit_code == 0
    assert "Existing" not in agents.read_text(encoding="utf-8")
    assert "QA-Z Merge Safety" in agents.read_text(encoding="utf-8")


def test_skill_install_append_adds_delimited_section(tmp_path: Path, capsys) -> None:
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# Existing\n", encoding="utf-8")

    exit_code = main(["skill", "install", "codex", "--path", str(tmp_path), "--append"])
    capsys.readouterr()
    text = agents.read_text(encoding="utf-8")

    assert exit_code == 0
    assert text.startswith("# Existing\n")
    assert "<!-- QA-Z MERGE SAFETY START -->" in text
    assert "<!-- QA-Z MERGE SAFETY END -->" in text


def test_skill_install_dry_run_does_not_write(tmp_path: Path, capsys) -> None:
    exit_code = main(
        ["skill", "install", "cursor", "--path", str(tmp_path), "--dry-run"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "would install cursor: .cursor/rules/qa-z.mdc" in output
    assert not (tmp_path / ".cursor").exists()


def test_skill_install_all_targets_create_expected_files(
    tmp_path: Path, capsys
) -> None:
    exit_code = main(["skill", "install", "all", "--path", str(tmp_path)])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "installed codex: AGENTS.md" in output
    assert "installed claude: CLAUDE.md" in output
    assert "installed cursor: .cursor/rules/qa-z.mdc" in output
    assert "installed copilot: .github/copilot-instructions.md" in output
    assert (tmp_path / "AGENTS.md").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".cursor" / "rules" / "qa-z.mdc").exists()
    assert (tmp_path / ".github" / "copilot-instructions.md").exists()


def test_skill_install_output_path_is_path_safe(tmp_path: Path, capsys) -> None:
    output_path = tmp_path / "nested" / "custom-agents.md"

    exit_code = main(
        [
            "skill",
            "install",
            "codex",
            "--path",
            str(tmp_path),
            "--output",
            str(output_path),
        ]
    )
    capsys.readouterr()

    assert exit_code == 0
    assert output_path.exists()
    assert "QA-Z Merge Safety" in output_path.read_text(encoding="utf-8")
