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
        "SUPPORT.md",
        ".github/ISSUE_TEMPLATE/config.yml",
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
        "docs/launch/actions-runtime-maintenance.md",
        "docs/launch/demo-gif-plan.md",
        "docs/launch/launch-post.md",
        "docs/launch/social-preview.md",
        "docs/walkthroughs/auth-bug.md",
        "docs/walkthroughs/pr-gate.md",
        "docs/walkthroughs/sarif-code-scanning.md",
        "docs/assets/qa-z-demo.cast",
        "docs/assets/qa-z-demo.svg",
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


def test_readme_demo_visual_is_checked_in_and_public_safe() -> None:
    readme = read("README.md")
    demo_cast_lines = read("docs/assets/qa-z-demo.cast").splitlines()
    demo_svg = read("docs/assets/qa-z-demo.svg")

    assert "Planned demo asset" not in readme
    assert "docs/assets/qa-z-demo.svg" in readme
    assert "docs/assets/qa-z-demo.cast" in readme
    assert "Run the auth-bug demo from the GitHub source install" in readme
    assert "Verdict: do_not_merge" in readme

    header = json.loads(demo_cast_lines[0])
    body = "\n".join(demo_cast_lines[1:])

    assert header["version"] == 2
    assert header["width"] == 100
    assert header["height"] == 28
    assert "timestamp" not in header
    for text in (
        "pipx install git+https://github.com/qazedhq/qa-z.git",
        "qa-z init --profile python --with-agent-templates",
        "qa-z doctor",
        "qa-z demo auth-bug",
        "cd .qa-z/demo/auth-bug",
        "qa-z guard --from-run latest --adapter codex",
        "Verdict: DO NOT MERGE YET",
        "qa-z repair-prompt --from-run latest --adapter codex",
    ):
        assert text in body
        assert text in demo_svg

    public_surfaces = "\n".join([readme, body, demo_svg])
    for forbidden in ("F:\\", "C:\\Users", "SECRET", "TOKEN", "BEGIN PRIVATE"):
        assert forbidden not in public_surfaces


def test_readme_short_quickstart_uses_runnable_demo_flow() -> None:
    readme = read("README.md")
    quickstart = readme.split("## Quickstart", 1)[1].split(
        "## GitHub Alpha Install", 1
    )[0]

    assert "qa-z init\nqa-z guard" not in quickstart
    for command in (
        "qa-z demo auth-bug",
        "qa-z demo auth-bug --json",
        "cd .qa-z/demo/auth-bug",
        "qa-z guard --from-run latest --adapter codex",
        "qa-z repair-prompt --from-run latest --adapter codex",
    ):
        assert command in quickstart
    assert "For your own repository" in quickstart
    assert "qa-z init --profile python --with-agent-templates" in quickstart


def test_docs_quickstart_leads_with_packaged_demo_before_example_repo_flow() -> None:
    quickstart = read("docs/quickstart.md")
    packaged_demo = quickstart.split("## Run The 60-Second Packaged Demo", 1)[1].split(
        "## Run The Example Repository Demo", 1
    )[0]

    for command in (
        "qa-z demo auth-bug",
        "qa-z demo auth-bug --json",
        "cd .qa-z/demo/auth-bug",
        "qa-z guard --from-run latest --adapter codex",
        "qa-z repair-prompt --from-run latest --adapter codex",
    ):
        assert command in packaged_demo

    assert "cd examples/agent-auth-bug" not in packaged_demo
    assert quickstart.index("qa-z demo auth-bug") < quickstart.index(
        "cd examples/agent-auth-bug"
    )


def test_examples_index_links_visual_proof_and_labels_run_status() -> None:
    examples_index = read("examples/README.md")
    agent_demo = read("examples/agent-auth-bug/README.md")
    fastapi_agent = read("examples/fastapi-agent-bug/README.md")
    ts_agent = read("examples/typescript-agent-bug/README.md")

    assert "## Visual proof" in examples_index
    assert "../docs/assets/qa-z-demo.svg" in examples_index
    assert "../docs/assets/qa-z-agent-auth-bug.cast" in examples_index
    assert "Runnable" in examples_index
    assert "| [nextjs-demo](nextjs-demo/) | Runnable |" in examples_index
    assert "Placeholder-only | Planned future Next.js" not in examples_index

    for doc in (agent_demo, fastapi_agent, ts_agent):
        assert "Terminal proof" in doc
        assert "qa-z-agent-auth-bug.cast" in doc
        assert "qa-z verify" in doc


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


def test_github_issue_templates_route_support_security_and_release_contacts() -> None:
    config = yaml.safe_load(read(".github/ISSUE_TEMPLATE/config.yml"))
    bug_report = yaml.safe_load(read(".github/ISSUE_TEMPLATE/bug_report.yml"))
    feature_request = yaml.safe_load(read(".github/ISSUE_TEMPLATE/feature_request.yml"))

    assert config["blank_issues_enabled"] is False
    contact_links = {link["name"]: link["url"] for link in config["contact_links"]}
    assert contact_links == {
        "Support questions": ("https://github.com/qazedhq/qa-z/blob/main/SUPPORT.md"),
        "Private security reports": (
            "https://github.com/qazedhq/qa-z/security/advisories/new"
        ),
        "Release, package, tag, or deploy approvals": (
            "https://github.com/qazedhq/qa-z/blob/main/docs/package-publish-plan.md"
        ),
    }

    bug_intro = bug_report["body"][0]["attributes"]["value"]
    feature_intro = feature_request["body"][0]["attributes"]["value"]
    assert "SUPPORT.md" in bug_intro
    assert "GitHub Security Advisory" in bug_intro
    assert "Release, package, tag, or deploy approvals" in feature_intro


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


def test_scorecard_docs_describe_permissions_triggers_and_local_limits() -> None:
    scorecard_docs = read("docs/scorecard.md")
    workflow = yaml.safe_load(read(".github/workflows/scorecard.yml"))
    triggers = workflow[True]

    assert {"schedule", "workflow_dispatch", "branch_protection_rule"} <= set(triggers)
    assert workflow["permissions"] == {
        "contents": "read",
        "security-events": "write",
    }

    scorecard_step = next(
        step
        for step in workflow["jobs"]["scorecard"]["steps"]
        if step.get("uses") == "ossf/scorecard-action@v2.4.0"
    )
    assert scorecard_step["with"]["publish_results"] is False
    assert scorecard_step["with"]["results_format"] == "sarif"

    for text in (
        "weekly schedule",
        "manual `workflow_dispatch`",
        "`branch_protection_rule` updates",
        "`contents: read`",
        "`security-events: write`",
        "`publish_results: false`",
        "does not post pull request comments",
        "Do not claim a current OpenSSF score from local validation.",
    ):
        assert text in scorecard_docs


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


def test_launch_issue_opening_handoff_points_to_full_seed_ledger() -> None:
    handoff = read("docs/launch/issues-to-open.md")
    issues = read("docs/issues/good-first-issues.md")

    assert "docs/issues/good-first-issues.md" in handoff
    assert "20 public-launch issue seeds" in handoff
    assert "https://github.com/qazedhq/qa-z/issues/28" in handoff
    assert "Existing overlapping issues were reused" in handoff
    assert "no open milestones" in handoff
    assert handoff.count("https://github.com/qazedhq/qa-z/issues/") >= issues.count(
        "## Issue "
    )


def test_launch_asset_docs_avoid_fabricated_public_claims() -> None:
    combined = "\n".join(
        [
            read("docs/launch/social-preview.md"),
            read("docs/launch/demo-gif-plan.md"),
            read("docs/launch/launch-post.md"),
        ]
    )

    assert "qa-z-social-preview.png" in combined
    assert "qa-z-demo.svg" in combined
    assert "QA-Z" in combined
    assert "Make AI coding safe to merge." in combined
    assert "qa-z-agent-auth-bug.cast" in combined
    assert "No package registry publish has happened yet." in combined
    assert "fake adoption" in combined


def test_social_preview_copy_matches_asset_and_stays_ascii_safe() -> None:
    social_preview = read("docs/launch/social-preview.md")
    launch_package = read("docs/launch-package.md")
    social_svg = read("docs/assets/qa-z-social-preview.svg")

    expected_lines = (
        "QA-Z",
        "Make AI coding safe to merge.",
        "Contracts. Checks. Repair prompts. Verification.",
    )

    for text in (social_preview, launch_package):
        for line in expected_lines:
            assert line in text
        assert all(ord(char) < 128 for char in text)

    assert "QA-Z social preview" in social_svg
    assert "Make AI coding safe to merge." in social_svg
    assert "Contracts. Checks. Repair prompts. Verification." in social_svg


def test_launch_package_pins_github_description_and_topics() -> None:
    launch_package = read("docs/launch-package.md")
    description = (
        "Make AI coding safe to merge. Deterministic QA contracts, checks, "
        "repair prompts, and verification for coding agents."
    )
    topics_block = launch_package.split("Recommended topics:", 1)[1].split(
        "## Social Preview", 1
    )[0]
    topics = [
        line.strip()
        for line in topics_block.splitlines()
        if line.strip() and not line.startswith("```")
    ]

    assert "## Repository Settings" in launch_package
    assert description in launch_package
    assert len(topics) == 20
    assert len(set(topics)) == len(topics)
    assert all(topic == topic.lower() for topic in topics)
    assert all(" " not in topic for topic in topics)
    assert {"ai-agents", "coding-agents", "sarif", "semgrep"} <= set(topics)
    assert "requires repository settings mutation" in launch_package
