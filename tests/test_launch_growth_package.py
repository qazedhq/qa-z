from __future__ import annotations

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_launch_growth_package_covers_requested_surfaces() -> None:
    required_paths = [
        "CODE_OF_CONDUCT.md",
        ".github/workflows/scorecard.yml",
        "templates/.github/workflows/qa-z-pr-comment.yml",
        "docs/launch-checklist.md",
        "docs/public-roadmap.md",
        "docs/package-publish-plan.md",
        "docs/use-with-semgrep.md",
        "docs/pr-summary-comment.md",
        "docs/agent-merge-safety-benchmark.md",
        "docs/scorecard.md",
        "docs/community-distribution.md",
        "docs/hosted-demo.md",
        "docs/docs-site.md",
        "docs/case-studies.md",
        "docs/monthly-benchmark-report-template.md",
        "docs/issues/good-first-issues.md",
        "docs/walkthroughs/auth-bug.md",
        "docs/walkthroughs/pr-gate.md",
        "docs/walkthroughs/sarif-code-scanning.md",
        "docs/assets/qa-z-agent-auth-bug.cast",
        "examples/fastapi-agent-bug/README.md",
        "examples/typescript-agent-bug/README.md",
    ]

    missing = [path for path in required_paths if not (ROOT / path).exists()]

    assert missing == []


def test_launch_checklist_maps_every_growth_phase_and_top_ten_item() -> None:
    checklist = read("docs/launch-checklist.md")

    for text in (
        "Phase 0 - 0 to 100 stars",
        "Phase 1 - 100 to 1,000 stars",
        "Phase 2 - 1,000 to 5,000 stars",
        "Phase 3 - 5,000 to 10,000 stars",
        "Phase 4 - 10,000 to 30,000 stars",
        "Week 1 - Repo polish",
        "Week 2 - Install and demo",
        "Week 3 - Distribution",
        "Week 4 - Credibility",
        "Top 10 immediate actions",
        "Killer feature candidates",
        "Do not do",
        "External blockers",
    ):
        assert text in checklist

    for number in range(1, 11):
        assert f"{number}." in checklist


def test_demo_asciinema_asset_is_real_cast_shape() -> None:
    lines = (
        (ROOT / "docs/assets/qa-z-agent-auth-bug.cast")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    header = json.loads(lines[0])
    body = "\n".join(lines[1:])

    assert header["version"] == 2
    assert header["width"] == 100
    assert header["height"] == 28
    assert "AI wrote a bad auth change. QA-Z caught it." in header["title"]
    assert "qa-z fast" in body
    assert "qa-z deep" in body
    assert "qa-z verify" in body
    assert "verdict: improved" in body


def test_agent_bug_examples_are_documented_and_configured() -> None:
    fastapi_config = yaml.safe_load(read("examples/fastapi-agent-bug/qa-z.yaml"))
    ts_config = yaml.safe_load(read("examples/typescript-agent-bug/qa-z.yaml"))

    assert [check["id"] for check in fastapi_config["fast"]["checks"]] == [
        "py_lint",
        "py_format",
        "py_test",
    ]
    assert [check["id"] for check in fastapi_config["deep"]["checks"]] == ["sg_scan"]
    assert [check["id"] for check in ts_config["fast"]["checks"]] == [
        "ts_lint",
        "ts_type",
        "ts_test",
    ]
    assert [check["id"] for check in ts_config["deep"]["checks"]] == ["sg_scan"]

    assert "FastAPI auth check" in read("examples/fastapi-agent-bug/README.md")
    assert "TypeScript agent bug" in read("examples/typescript-agent-bug/README.md")


def test_docs_index_and_readme_link_full_growth_package() -> None:
    combined = read("README.md") + "\n" + read("docs/README.md")

    for link in (
        "docs/launch-checklist.md",
        "docs/public-roadmap.md",
        "docs/package-publish-plan.md",
        "docs/use-with-semgrep.md",
        "docs/pr-summary-comment.md",
        "docs/agent-merge-safety-benchmark.md",
        "docs/scorecard.md",
        "docs/community-distribution.md",
    ):
        assert link in combined


def test_optional_pr_comment_and_scorecard_surfaces_are_opt_in() -> None:
    pr_comment = read("templates/.github/workflows/qa-z-pr-comment.yml")
    scorecard = read(".github/workflows/scorecard.yml")

    assert "QA_Z_POST_PR_COMMENT" in pr_comment
    assert "pull-requests: write" in pr_comment
    assert "do not enable this template unless" in pr_comment.lower()
    assert "ossf/scorecard-action" in scorecard
    assert "security-events: write" in scorecard


def test_good_first_issue_seed_count_and_specificity() -> None:
    issues = read("docs/issues/good-first-issues.md")

    assert issues.count("## Issue ") >= 20
    for text in (
        "Files",
        "Acceptance",
        "Validation",
        "examples/agent-auth-bug",
        "examples/typescript-agent-bug",
        "OpenSSF Scorecard",
    ):
        assert text in issues
