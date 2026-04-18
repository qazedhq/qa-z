"""Tests for QA-Z GitHub workflow summary wiring."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ci_workflow_writes_github_summary() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "python -m qa_z github-summary --from-run .qa-z/runs/ci" in workflow
    assert "$GITHUB_STEP_SUMMARY" in workflow


def test_template_workflow_writes_github_summary() -> None:
    workflow = (ROOT / "templates" / ".github" / "workflows" / "vibeqa.yml").read_text(
        encoding="utf-8"
    )

    assert "qa-z github-summary --from-run latest" in workflow
    assert "$GITHUB_STEP_SUMMARY" in workflow
