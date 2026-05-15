from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_pr_comment_docs_explain_dry_run_and_permission_boundary() -> None:
    docs = read("docs/pr-summary-comment.md")

    for text in (
        "QA_Z_POST_PR_COMMENT=false",
        "Default Dry Run",
        "no pull request comment is created",
        "Permission Tradeoff",
        "pull-requests: write",
        "bot-comment behavior",
        "docs/assets/pr-comment-dry-run-capture.md",
    ):
        assert text in docs


def test_pr_comment_dry_run_capture_is_sanitized() -> None:
    capture = read("docs/assets/pr-comment-dry-run-capture.md")

    for text in (
        "sanitized textual capture",
        "QA_Z_POST_PR_COMMENT=false",
        "Build optional PR comment body",
        "skipped",
        "Post optional PR comment",
        "GitHub pull request comment created",
        "no",
        "Private data intentionally omitted",
        "tokens",
        "secret",
        "user emails",
    ):
        assert text in capture


def test_pr_comment_template_defaults_to_no_posting() -> None:
    workflow: dict[str, Any] = yaml.safe_load(
        read("templates/.github/workflows/qa-z-pr-comment.yml")
    )

    assert workflow["env"]["QA_Z_POST_PR_COMMENT"] == "false"

    job = workflow["jobs"]["qa-z-comment"]
    assert job["permissions"]["pull-requests"] == "write"

    build_step = next(
        step
        for step in job["steps"]
        if step["name"] == "Build optional PR comment body"
    )
    post_step = next(
        step for step in job["steps"] if step["name"] == "Post optional PR comment"
    )

    expected_guard = "${{ always() && env.QA_Z_POST_PR_COMMENT == 'true' }}"
    assert build_step["if"] == expected_guard
    assert post_step["if"] == expected_guard
