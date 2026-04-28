"""Architecture tests for GitHub-summary command context helpers."""

from __future__ import annotations

import qa_z.commands.review_github_context as review_github_context_module


def test_review_github_context_module_exposes_context_helpers() -> None:
    assert callable(review_github_context_module.resolve_github_summary_run_source)
    assert callable(review_github_context_module.load_github_summary_context)
