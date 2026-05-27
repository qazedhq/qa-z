from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_scorecard_docs_explain_first_run_and_follow_up_tasks() -> None:
    docs = read("docs/scorecard.md")

    for text in (
        "QA-Z Scorecard",
        "qa-z scorecard",
        "qa-z scorecard --json",
        "read-only unless `--output` is supplied",
        "benchmark, create `.qa-z/**`",
        "Production PyPI is not published.",
        "PyPI install claim.",
        "`project_config`",
        "`deep_semgrep`",
        "`benchmark_corpus`",
        "`evidence_freshness`",
        "Missing `qa-z.yaml`: run `qa-z init`.",
        "OpenSSF Scorecard",
        "Inspect The First Run",
        "scorecard-results.sarif",
        "openssf-scorecard",
        "GitHub code scanning",
        "Turn Scorecard Findings Into QA-Z Tasks",
        "deterministic follow-up task",
        "finding source",
        "affected file or repository setting",
        "validation command",
        "non-goals",
        "Follow-up Issue Template",
        "Do not claim a current OpenSSF score from local validation.",
        "Do not add or advertise a numeric Scorecard badge",
    ):
        assert text in docs


def test_scorecard_workflow_stays_least_privilege_and_boundaries_are_documented() -> (
    None
):
    workflow: dict[str, Any] = yaml.safe_load(read(".github/workflows/scorecard.yml"))
    docs = read("docs/scorecard.md")

    assert workflow["permissions"] == {
        "contents": "read",
        "security-events": "write",
    }

    scorecard_step = next(
        step
        for step in workflow["jobs"]["scorecard"]["steps"]
        if step["name"] == "Run OpenSSF Scorecard"
    )
    assert scorecard_step["uses"] == "ossf/scorecard-action@v2.4.0"
    assert scorecard_step["with"]["publish_results"] is False

    upload_step = next(
        step
        for step in workflow["jobs"]["scorecard"]["steps"]
        if step["name"] == "Upload Scorecard SARIF"
    )
    assert upload_step["uses"] == "github/codeql-action/upload-sarif@v4"
    assert upload_step["with"]["sarif_file"] == "scorecard-results.sarif"
    assert upload_step["with"]["category"] == "openssf-scorecard"

    for boundary in (
        "does not post pull request comments",
        "create branches",
        "commit",
        "push",
        "tag",
        "publish packages",
        "deploy",
        "live coding agents",
    ):
        assert boundary in docs
