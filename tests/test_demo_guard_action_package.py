"""Tests for demo, action, skill-pack, and install-smoke public surfaces."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from qa_z.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_demo_auth_bug_command_writes_repair_and_guard_artifacts(
    tmp_path: Path, capsys
) -> None:
    exit_code = main(["demo", "auth-bug", "--path", str(tmp_path)])
    output = capsys.readouterr().out
    demo = tmp_path / ".qa-z" / "demo" / "auth-bug"
    verdict_path = demo / ".qa-z" / "runs" / "latest" / "guard" / "verdict.json"

    assert exit_code == 0
    assert "AI wrote a risky auth change. QA-Z caught it before merge." in output
    assert verdict_path.exists()
    assert json.loads(verdict_path.read_text(encoding="utf-8"))["status"] == (
        "do_not_merge"
    )
    assert (demo / ".qa-z" / "runs" / "latest" / "repair" / "codex.md").exists()


def test_agent_skill_pack_and_templates_exist() -> None:
    required_paths = [
        "skills/qa-z-merge-safety/SKILL.md",
        "skills/qa-z-merge-safety/README.md",
        "skills/qa-z-merge-safety/examples/codex.md",
        "skills/qa-z-merge-safety/examples/claude-code.md",
        "skills/qa-z-merge-safety/examples/cursor.md",
        "templates/AGENTS.qa-z.md",
        "templates/CLAUDE.qa-z.md",
        "templates/CURSOR.qa-z.mdc",
        "templates/COPILOT.qa-z.instructions.md",
        ".github/actions/guard/README.md",
        "docs/agent-qa-playbook.md",
        "docs/ai-code-merge-checklist.md",
        "docs/bad-ai-code-examples.md",
        "docs/codex-repair-recipes.md",
        "docs/claude-code-repair-recipes.md",
        "docs/cursor-safety-rules.md",
        "docs/semgrep-for-ai-generated-code.md",
        "docs/use-with-github-copilot.md",
        "examples/agent-auth-bug/repo/README.md",
        "examples/agent-auth-bug/repo/app/auth.py",
        "examples/agent-auth-bug/repo/tests/test_auth.py",
        "examples/agent-auth-bug/repo/qa-z.yaml",
    ]

    for relative in required_paths:
        assert (ROOT / relative).is_file(), relative

    skill = (ROOT / "skills" / "qa-z-merge-safety" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert skill.startswith("---\nname: qa-z-merge-safety\n")
    assert "Do not claim code is safe without evidence." in skill


def test_packaged_skill_pack_matches_public_source_pack() -> None:
    public_skill = ROOT / "skills" / "qa-z-merge-safety"
    packaged_skill = (
        ROOT / "src" / "qa_z" / "templates" / "skills" / ("qa-z-merge-safety")
    )
    relative_paths = [
        "SKILL.md",
        "README.md",
        "examples/codex.md",
        "examples/claude-code.md",
        "examples/cursor.md",
    ]

    for relative in relative_paths:
        assert (packaged_skill / relative).read_text(encoding="utf-8") == (
            public_skill / relative
        ).read_text(encoding="utf-8")


def test_guard_composite_action_and_example_workflow_are_parseable() -> None:
    action = yaml.safe_load(
        (ROOT / ".github" / "actions" / "guard" / "action.yml").read_text(
            encoding="utf-8"
        )
    )
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "qa-z-example.yml.example").read_text(
            encoding="utf-8"
        )
    )

    assert action["name"] == "QA-Z Guard"
    assert action["inputs"]["deep"]["default"] == "auto"
    assert action["inputs"]["profile"]["default"] == "python"
    assert action["inputs"]["adapter"]["default"] == "codex"
    assert action["inputs"]["upload-sarif"]["default"] == "false"
    runs = "\n".join(step.get("run", "") for step in action["runs"]["steps"])
    assert "qa-z doctor" in runs
    assert "qa-z guard --deep" in runs
    assert "inputs.profile" in runs
    assert workflow["jobs"]["qa-z"]["permissions"]["contents"] == "read"
    assert "security-events" not in workflow["jobs"]["qa-z"]["permissions"]


def test_public_install_docs_and_readme_reference_guard_and_skill_pack() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    github_action = (ROOT / "docs" / "github-action.md").read_text(encoding="utf-8")
    cursor_docs = (ROOT / "docs" / "use-with-cursor.md").read_text(encoding="utf-8")
    case_studies = (ROOT / "docs" / "case-studies.md").read_text(encoding="utf-8")

    assert "Make AI coding safe to merge." in readme
    assert readme.startswith("# QA-Z 🛡️\n\n> Make AI coding safe to merge.\n")
    assert "docs/assets/qa-z-demo.gif" in readme
    assert "qa-z guard" in readme
    assert "qa-z skill install all" in readme
    assert "pipx install git+https://github.com/qazedhq/qa-z.git" in readme
    assert "uv tool install git+https://github.com/qazedhq/qa-z.git" in readme
    assert "qazedhq/qa-z/.github/actions/guard@main" in github_action
    readme_action_section = readme.split("## GitHub Action", 1)[1].split(
        "## Agent QA Playbook", 1
    )[0]
    readme_action_yaml = readme_action_section.split("```yaml", 1)[1].split("```", 1)[0]
    assert "security-events: write" not in readme_action_yaml
    assert readme.index("## Quickstart") < readme.index("## GitHub Alpha Install")
    assert readme.index("## GitHub Alpha Install") < readme.index("## Why QA-Z?")
    assert "--adapter handoff" not in cursor_docs
    assert "Hypothetical seed: a team installed the QA-Z GitHub Action." in (
        case_studies
    )
