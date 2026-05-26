"""Tests for optional qa-z init outputs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from qa_z.cli import main


@pytest.fixture(autouse=True)
def stable_doctor_tool_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep init tests focused on generated files, not host tool availability."""
    monkeypatch.setattr("qa_z.doctor.find_executable", lambda name: name)


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


def test_init_with_agent_templates_passes_doctor(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path), "--with-agent-templates"])
    capsys.readouterr()

    assert exit_code == 0

    doctor_exit = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert doctor_exit == 0
    assert payload["status"] == "passed"
    assert payload["errors"] == []
    assert payload["warnings"] == []


def test_init_without_agent_templates_surfaces_repairable_doctor_warning(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path)])
    capsys.readouterr()

    assert exit_code == 0

    doctor_exit = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert doctor_exit == 0
    assert payload["status"] == "warning"
    assert {warning["code"] for warning in payload["warnings"]} == {
        "missing_instruction_file"
    }
    assert "qa-z init --with-agent-templates" in payload["suggestions"]


def test_init_without_agent_templates_strict_fails_for_missing_instruction_files(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path)])
    capsys.readouterr()

    assert exit_code == 0

    doctor_exit = main(["doctor", "--path", str(tmp_path), "--strict"])
    output = capsys.readouterr().out

    assert doctor_exit == 1
    assert "warning missing_instruction_file" in output


@pytest.mark.parametrize(
    "profile",
    ("default", "python", "typescript", "nextjs", "monorepo", "mixed", "unknown"),
)
def test_init_profile_with_agent_templates_passes_doctor(
    profile: str,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "init",
            "--path",
            str(tmp_path),
            "--profile",
            profile,
            "--with-agent-templates",
        ]
    )
    capsys.readouterr()

    assert exit_code == 0

    doctor_exit = main(["doctor", "--path", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert doctor_exit == 0
    assert payload["status"] == "passed"
    assert payload["errors"] == []
    assert payload["warnings"] == []


def test_init_with_all_optional_outputs_passes_strict_doctor(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "init",
            "--path",
            str(tmp_path),
            "--with-agent-templates",
            "--with-github-workflow",
        ]
    )
    capsys.readouterr()

    assert exit_code == 0

    doctor_exit = main(["doctor", "--path", str(tmp_path), "--strict", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert doctor_exit == 0
    assert payload["status"] == "passed"
    assert payload["errors"] == []
    assert payload["warnings"] == []


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


def test_init_with_profile_nextjs_marks_nextjs_assumptions(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path), "--profile", "nextjs"])
    capsys.readouterr()
    config = load_initialized_config(tmp_path)

    assert exit_code == 0
    assert config["project"]["profile"] == "nextjs"  # type: ignore[index]
    assert config["project"]["languages"] == ["typescript"]  # type: ignore[index]
    assert [
        check["id"]
        for check in config["fast"]["checks"]  # type: ignore[index]
    ] == ["ts_lint", "ts_type", "ts_test"]


def test_init_with_profile_mixed_uses_smart_selection(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path), "--profile", "mixed"])
    capsys.readouterr()
    config = load_initialized_config(tmp_path)

    assert exit_code == 0
    assert config["project"]["profile"] == "mixed"  # type: ignore[index]
    assert config["project"]["languages"] == ["python", "typescript"]  # type: ignore[index]
    assert config["fast"]["selection"]["default_mode"] == "smart"  # type: ignore[index]


def test_init_auto_writes_detected_python_profile(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'demo'\n", encoding="utf-8"
    )

    exit_code = main(["init", "--path", str(tmp_path), "--profile", "auto"])
    output = capsys.readouterr().out
    config = load_initialized_config(tmp_path)

    assert exit_code == 0
    assert "QA-Z init profile detection: python" in output
    assert "created: qa-z.yaml" in output
    assert config["project"]["profile"] == "python"  # type: ignore[index]
    assert config["project"]["languages"] == ["python"]  # type: ignore[index]


def test_init_auto_explain_prints_evidence_when_writing(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"next":"15.0.0"}}\n',
        encoding="utf-8",
    )
    (tmp_path / "next.config.js").write_text("module.exports = {}\n", encoding="utf-8")

    exit_code = main(
        ["init", "--path", str(tmp_path), "--profile", "auto", "--explain"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "QA-Z init profile detection: nextjs" in output
    assert "evidence: package.json, next.config.js" in output
    assert "activated checks: Next.js TypeScript surface" in output


def test_init_with_github_workflow_creates_workflow(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["init", "--path", str(tmp_path), "--with-github-workflow"])
    output = capsys.readouterr().out

    workflow = tmp_path / ".github" / "workflows" / "qa-z.yml"
    workflow_text = workflow.read_text(encoding="utf-8")
    workflow_config = yaml.safe_load(workflow_text)
    qa_z_job = workflow_config["jobs"]["qa-z"]
    steps = qa_z_job["steps"]

    assert exit_code == 0
    assert workflow.is_file()
    assert workflow_config["permissions"] == {"contents": "read"}
    assert qa_z_job["timeout-minutes"] == 15
    assert [step["name"] for step in steps] == [
        "Checkout repository",
        "Set up Python",
        "Install QA-Z",
        "Validate QA-Z config",
        "Run QA-Z fast gate",
    ]
    assert "permissions:\n  contents: read\n" in workflow_text
    assert "timeout-minutes: 15\n" in workflow_text
    assert "persist-credentials: false\n" in workflow_text
    assert "name: Checkout repository\n" in workflow_text
    assert "name: Set up Python\n" in workflow_text
    assert "name: Install QA-Z\n" in workflow_text
    assert "name: Validate QA-Z config\n" in workflow_text
    assert "name: Run QA-Z fast gate\n" in workflow_text
    assert (
        'python -m pip install "git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha"'
        in workflow_text
    )
    assert "python -m pip install -e .[dev]" not in workflow_text
    assert "python -m qa_z doctor --json" in workflow_text
    assert workflow_text.index("python -m qa_z doctor --json") < workflow_text.index(
        "python -m qa_z fast --json"
    )
    assert "python -m qa_z fast --json" in workflow_text
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

    doctor_exit = main(["doctor", "--path", str(tmp_path), "--strict", "--json"])
    payload = json.loads(capsys.readouterr().out)

    assert doctor_exit == 0
    assert payload["status"] == "passed"
