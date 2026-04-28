"""Mixed-surface coverage policy tests for self-improvement."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.self_improvement import BacklogCandidate, run_self_inspection, score_candidate
from tests.self_improvement_test_support import (
    write_fixture_expectation,
    write_fixture_index,
)


NOW = "2026-04-15T00:00:00Z"


def test_score_candidate_boosts_reseed_and_service_readiness_signals() -> None:
    candidate = BacklogCandidate(
        id="coverage_gap-mixed-surface-benchmark-realism",
        title="Expand executed mixed-surface benchmark realism",
        category="coverage_gap",
        evidence=[
            {
                "source": "roadmap",
                "path": "docs/reports/next-improvement-roadmap.md",
                "summary": "mixed-surface executed benchmark expansion remains open",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=3,
        repair_cost=5,
        recommendation="add_benchmark_fixture",
        signals=[
            "mixed_surface_realism_gap",
            "roadmap_gap",
            "service_readiness_gap",
            "recent_empty_loop_chain",
        ],
        recurrence_count=2,
    )

    score = score_candidate(candidate)

    assert score == 52


def test_self_inspection_keeps_coverage_gap_when_mixed_fixture_only_covers_fast_and_handoff(
    tmp_path: Path,
) -> None:
    write_fixture_expectation(
        tmp_path,
        "mixed_fast_handoff_functional_worktree_cleanup",
        {
            "name": "mixed_fast_handoff_functional_worktree_cleanup",
            "run": {"fast": True, "repair_handoff": True},
            "expect_fast": {"status": "failed"},
            "expect_handoff": {"summary_contains": ["cleanup"]},
        },
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="mixed-executed-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    categories = {candidate["category"] for candidate in report["candidates"]}

    assert "coverage_gap" in categories


def test_self_inspection_skips_coverage_gap_when_fast_deep_and_handoff_mixed_fixtures_exist(
    tmp_path: Path,
) -> None:
    write_fixture_index(tmp_path, ["py_type_error"])
    write_fixture_expectation(
        tmp_path,
        "mixed_fast_functional_worktree_cleanup",
        {
            "name": "mixed_fast_functional_worktree_cleanup",
            "run": {"fast": True},
            "expect_fast": {"status": "failed"},
        },
    )
    write_fixture_expectation(
        tmp_path,
        "mixed_deep_functional_worktree_cleanup",
        {
            "name": "mixed_deep_functional_worktree_cleanup",
            "run": {"deep": True},
            "expect_deep": {"status": "failed"},
        },
    )
    write_fixture_expectation(
        tmp_path,
        "mixed_handoff_functional_worktree_cleanup",
        {
            "name": "mixed_handoff_functional_worktree_cleanup",
            "run": {"repair_handoff": True},
            "expect_handoff": {"summary_contains": ["cleanup"]},
        },
    )

    paths = run_self_inspection(
        root=tmp_path,
        now=NOW,
        loop_id="mixed-fully-executed-loop",
    )
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    categories = {candidate["category"] for candidate in report["candidates"]}

    assert "coverage_gap" not in categories
