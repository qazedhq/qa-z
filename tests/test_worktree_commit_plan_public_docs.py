"""Commit-plan tests for public repository docs and community health files."""

from __future__ import annotations

from tests.worktree_commit_plan_test_support import load_plan_module


def test_commit_plan_routes_public_support_docs_to_current_truth_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? SUPPORT.md",
            " M SECURITY.md",
            " M CONTRIBUTING.md",
            " M CODE_OF_CONDUCT.md",
            " M docs/ai-code-merge-checklist.md",
            " M docs/bad-ai-code-examples.md",
            " M docs/comparison.md",
            " M docs/README.md",
            " M docs/product/PRODUCT_DIRECTION.md",
            " M docs/roadmap.md",
            "?? docs/use-with-aider.md",
            "?? docs/use-with-openhands.md",
            "?? docs/use-with-goose.md",
            " M tests/test_public_docs_current_truth.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["current_truth_release_surface"]["changed_paths"] == [
        "SUPPORT.md",
        "SECURITY.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "docs/ai-code-merge-checklist.md",
        "docs/bad-ai-code-examples.md",
        "docs/comparison.md",
        "docs/README.md",
        "docs/product/PRODUCT_DIRECTION.md",
        "docs/roadmap.md",
        "docs/use-with-aider.md",
        "docs/use-with-openhands.md",
        "docs/use-with-goose.md",
        "tests/test_public_docs_current_truth.py",
    ]
    assert result["unassigned_source_paths"] == []
    assert result["cross_cutting_paths"] == []
    assert result["status"] == "ready"


def test_commit_plan_routes_github_community_templates_to_current_truth_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? .github/ISSUE_TEMPLATE/config.yml",
            " M .github/ISSUE_TEMPLATE/bug_report.yml",
            " M .github/ISSUE_TEMPLATE/feature_request.yml",
            " M .github/pull_request_template.md",
            " M tests/test_launch_growth_package.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["current_truth_release_surface"]["changed_paths"] == [
        ".github/ISSUE_TEMPLATE/config.yml",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/pull_request_template.md",
        "tests/test_launch_growth_package.py",
    ]
    assert result["unassigned_source_paths"] == []
    assert result["cross_cutting_paths"] == []
    assert result["status"] == "ready"
