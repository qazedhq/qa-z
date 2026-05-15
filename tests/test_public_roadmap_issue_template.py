from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_yaml(path: str) -> dict[str, Any]:
    return yaml.safe_load(read(path))


def fields_by_id(template: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in template["body"] if "id" in item}


def test_public_roadmap_issue_template_requires_evidence_validation_and_impact() -> (
    None
):
    template = load_yaml(".github/ISSUE_TEMPLATE/roadmap_proposal.yml")

    assert template["name"] == "Public roadmap proposal"
    assert template["title"] == "[Roadmap]: "
    assert "enhancement" in template["labels"]
    assert "docs" in template["labels"]

    fields = fields_by_id(template)

    for field_id in (
        "proposal",
        "roadmap_area",
        "user_impact",
        "evidence",
        "validation",
        "non_goals",
        "boundaries",
    ):
        assert field_id in fields

    for field_id in (
        "proposal",
        "roadmap_area",
        "user_impact",
        "evidence",
        "validation",
        "non_goals",
    ):
        assert fields[field_id]["validations"]["required"] is True

    validation = fields["validation"]["attributes"]
    assert validation["render"] == "bash"


def test_public_roadmap_template_prevents_release_and_live_automation_overclaims() -> (
    None
):
    template = load_yaml(".github/ISSUE_TEMPLATE/roadmap_proposal.yml")
    fields = fields_by_id(template)
    options = fields["boundaries"]["attributes"]["options"]
    labels = "\n".join(option["label"] for option in options)

    for required_boundary in (
        "live Codex, Claude, or other model execution",
        "PyPI/TestPyPI/package-registry publishing",
        "tag, release, deployment, branch mutation, or bot-comment automation",
        "deterministic evidence and validation",
        "Generated `.qa-z/**`, `build/**`, `dist/**`, cache, and benchmark runtime artifacts",
    ):
        assert required_boundary in labels

    assert all(option["required"] is True for option in options)


def test_public_roadmap_docs_link_to_roadmap_proposal_template() -> None:
    docs = read("docs/public-roadmap.md")

    assert ".github/ISSUE_TEMPLATE/roadmap_proposal.yml" in docs
    assert "A roadmap proposal must include" in docs
    assert "user impact" in docs
    assert "deterministic validation commands" in docs
    assert "Roadmap proposals do not approve package publishing" in docs
    assert "live model execution" in docs
    assert "bot comments" in docs


def test_issue_template_config_keeps_blank_issues_disabled() -> None:
    config = load_yaml(".github/ISSUE_TEMPLATE/config.yml")

    assert config["blank_issues_enabled"] is False
