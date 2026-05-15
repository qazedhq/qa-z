from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_yaml(path: str) -> dict[str, Any]:
    return yaml.safe_load(read(path))


def test_github_action_docs_explain_job_summary_and_artifact_pointers() -> None:
    docs = read("docs/github-action.md")

    for text in (
        "Job Summary And Artifact Pointers",
        ".qa-z/runs/latest/guard/github-summary.md",
        ".qa-z/runs/latest/guard/verdict.md",
        "qa-z-runs",
        ".qa-z/runs/latest",
        "docs/assets/github-actions-summary-capture.md",
        "deterministic review surface",
    ):
        assert text in docs


def test_github_actions_summary_capture_is_sanitized_and_actionable() -> None:
    capture = read("docs/assets/github-actions-summary-capture.md")

    for text in (
        "sanitized textual capture",
        "QA-Z Summary",
        "Artifact: qa-z-runs",
        ".qa-z/runs/latest/guard/github-summary.md",
        ".qa-z/runs/latest/guard/verdict.md",
        ".qa-z/runs/latest/fast/summary.json",
        ".qa-z/runs/latest/deep/summary.json",
        ".qa-z/runs/latest/repair/codex.md",
        ".qa-z/runs/latest/deep/results.sarif",
        "Reviewer path",
        "Private data intentionally omitted",
        "token values",
        "secret names or values",
        "does not post a PR comment",
        "does not commit, push, tag, release, deploy, publish packages, or call live model APIs",
    ):
        assert text in capture


def test_guard_action_publishes_summary_and_artifact_contract() -> None:
    action = load_yaml(".github/actions/guard/action.yml")
    steps = action["runs"]["steps"]

    summary_step = next(
        step for step in steps if step.get("name") == "Publish QA-Z summary"
    )
    artifact_step = next(
        step for step in steps if step.get("name") == "Upload QA-Z artifacts"
    )

    assert summary_step["if"] == "${{ always() }}"
    assert "$GITHUB_STEP_SUMMARY" in summary_step["run"]
    assert ".qa-z/runs/latest/guard/github-summary.md" in summary_step["run"]
    assert ".qa-z/runs/latest/guard/verdict.md" in summary_step["run"]

    assert artifact_step["if"] == "${{ always() }}"
    assert artifact_step["uses"] == "actions/upload-artifact@v6"
    assert artifact_step["with"]["name"] == "qa-z-runs"
    assert artifact_step["with"]["path"] == ".qa-z/runs/latest"
    assert artifact_step["with"]["retention-days"] == 7
