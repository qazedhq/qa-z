"""Scoring and path-classification tests for self-improvement."""

from __future__ import annotations

from qa_z.self_improvement import (
    BacklogCandidate,
    classify_worktree_path_area,
    score_candidate,
)


def test_score_candidate_uses_formula_and_grounded_bonuses() -> None:
    candidate = BacklogCandidate(
        id="verify_regression-candidate",
        title="Stabilize regressed verification verdict",
        category="verify_regression",
        evidence=[
            {
                "source": "verification",
                "path": ".qa-z/runs/candidate/verify/summary.json",
                "summary": "verdict=regressed",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=3,
        repair_cost=5,
        recommendation="stabilize_verification_surface",
        signals=["verify_regressed", "regression_prevention"],
        recurrence_count=2,
    )

    score = score_candidate(candidate)

    assert score == 47


def test_classify_worktree_path_area_uses_stable_repository_buckets() -> None:
    assert classify_worktree_path_area(".github/workflows/ci.yml") == "workflow"
    assert classify_worktree_path_area("src/qa_z/cli.py") == "source"
    assert classify_worktree_path_area("tests/test_cli.py") == "tests"
    assert (
        classify_worktree_path_area("docs/reports/current-state-analysis.md") == "docs"
    )
    assert classify_worktree_path_area("README.md") == "docs"
    assert (
        classify_worktree_path_area("benchmarks/fixtures/example/expected.json")
        == "benchmark"
    )
    assert classify_worktree_path_area("benchmark/README.md") == "benchmark"
    assert classify_worktree_path_area("examples/fastapi-demo/README.md") == "examples"
    assert classify_worktree_path_area("templates/AGENTS.md") == "templates"
    assert classify_worktree_path_area("pyproject.toml") == "config"
    assert (
        classify_worktree_path_area(".qa-z/loops/latest/outcome.json")
        == "runtime_artifact"
    )
    assert classify_worktree_path_area("scripts/local-tool.py") == "other"
