"""Behavioral tests for worktree discovery candidate assembly."""

from __future__ import annotations

from pathlib import Path

from qa_z.worktree_discovery import discover_worktree_risk_candidates
from qa_z.live_repository import has_commit_isolation_worktree_pressure
from qa_z.live_repository import has_cleanup_artifact_pressure
from qa_z.live_repository_render import classify_worktree_path_area
from qa_z.live_repository_render import is_runtime_artifact_path
from tests.self_improvement_test_support import write_report


NOW = "2026-04-23T10:00:00Z"
UTC_LATE = "2026-04-22T20:21:42Z"
HEAD = "1234567890abcdef1234567890abcdef12345678"


def live_signals() -> dict[str, object]:
    """Return a dirty-worktree signal set above the worktree-risk threshold."""
    return {
        "current_branch": "codex/qa-z-bootstrap",
        "current_head": HEAD,
        "modified_count": 16,
        "untracked_count": 18,
        "staged_count": 0,
        "modified_paths": [
            "README.md",
            "docs/reports/current-state-analysis.md",
            "src/qa_z/autonomy_actions.py",
        ],
        "untracked_paths": [
            "tests/test_autonomy.py",
            "tests/test_worktree_discovery_candidates.py",
        ],
    }


def test_worktree_risk_candidates_attach_fresh_commit_plan_evidence(
    tmp_path: Path,
) -> None:
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        f"""
        # QA-Z Worktree Commit Plan

        Date: 2026-04-23
        Branch: `codex/qa-z-bootstrap`
        Head: `{HEAD}`

        This report calls out commit split ordering for the dirty worktree.
        """,
    )

    candidates = discover_worktree_risk_candidates(
        tmp_path, live_signals(), generated_at=UTC_LATE
    )

    assert len(candidates) == 1
    evidence = candidates[0].evidence
    assert evidence[0] == {
        "source": "git_status",
        "path": ".",
        "summary": (
            "modified=16; untracked=18; staged=0; "
            "areas=docs:2, tests:2, source:1; "
            "sample=README.md, docs/reports/current-state-analysis.md, "
            "src/qa_z/autonomy_actions.py"
        ),
    }
    assert {
        "source": "worktree_commit_plan",
        "path": "docs/reports/worktree-commit-plan.md",
        "summary": "report calls out worktree integration or commit-split risk",
    } in evidence
    assert {
        "source": "worktree_commit_plan",
        "path": "docs/reports/worktree-commit-plan.md",
        "summary": (
            "report freshness verified: date~=2026-04-23; "
            "branch=codex/qa-z-bootstrap; "
            f"head={HEAD}"
        ),
    } in evidence


def test_worktree_risk_candidates_skip_stale_commit_plan_evidence(
    tmp_path: Path,
) -> None:
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Date: 2026-04-21
        Branch: `codex/qa-z-bootstrap`

        This report calls out commit split ordering for the dirty worktree.
        """,
    )

    candidates = discover_worktree_risk_candidates(
        tmp_path, live_signals(), generated_at=UTC_LATE
    )

    assert len(candidates) == 1
    assert candidates[0].evidence == [
        {
            "source": "git_status",
            "path": ".",
            "summary": (
                "modified=16; untracked=18; staged=0; "
                "areas=docs:2, tests:2, source:1; "
                "sample=README.md, docs/reports/current-state-analysis.md, "
                "src/qa_z/autonomy_actions.py"
            ),
        }
    ]


def test_worktree_risk_candidates_accept_adjacent_date_current_state_reports(
    tmp_path: Path,
) -> None:
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-23
        Branch context: `codex/qa-z-bootstrap`

        Integration-gap candidates should use live git evidence instead of
        stale report-only wording when dirty worktree integration caveats remain.
        """,
    )

    candidates = discover_worktree_risk_candidates(
        tmp_path, live_signals(), generated_at=UTC_LATE
    )

    assert len(candidates) == 1
    assert {
        "source": "current_state",
        "path": "docs/reports/current-state-analysis.md",
        "summary": "report calls out worktree integration or commit-split risk",
    } in candidates[0].evidence
    assert {
        "source": "current_state",
        "path": "docs/reports/current-state-analysis.md",
        "summary": (
            "report freshness verified: date~=2026-04-23; branch=codex/qa-z-bootstrap"
        ),
    } in candidates[0].evidence


def test_literal_percent_temp_benchmark_output_is_runtime_artifact_pressure() -> None:
    path = "%TEMP%/qa-z-l27-full-benchmark/report.md"
    live_signals = {
        "modified_paths": [],
        "untracked_paths": [path],
        "runtime_artifact_paths": [path],
        "benchmark_result_paths": [],
        "generated_artifact_policy_explicit": True,
    }

    assert is_runtime_artifact_path(path)
    assert classify_worktree_path_area(path) == "runtime_artifact"
    assert has_cleanup_artifact_pressure(live_signals)
    assert not has_commit_isolation_worktree_pressure(live_signals)


def test_mypy_safe_cache_is_runtime_artifact_pressure() -> None:
    path = ".mypy_cache_safe/3.10/cache.db"
    live_signals = {
        "modified_paths": [],
        "untracked_paths": [path],
        "runtime_artifact_paths": [path],
        "benchmark_result_paths": [],
        "generated_artifact_policy_explicit": True,
    }

    assert is_runtime_artifact_path(path)
    assert classify_worktree_path_area(path) == "runtime_artifact"
    assert has_cleanup_artifact_pressure(live_signals)
    assert not has_commit_isolation_worktree_pressure(live_signals)


def test_local_only_generated_roots_are_runtime_artifact_pressure() -> None:
    paths = [
        ".ruff_cache_safe/CACHEDIR.TAG",
        ".pytest_cache/v/cache/nodeids",
        "build/lib/qa_z/__init__.py",
        "dist/qa_z-0.9.8.tar.gz",
        "src/qa_z.egg-info/PKG-INFO",
        "src/qa_z/__pycache__/cli.cpython-310.pyc",
    ]

    live_signals = {
        "modified_paths": [],
        "untracked_paths": paths,
        "runtime_artifact_paths": paths,
        "benchmark_result_paths": [],
        "generated_artifact_policy_explicit": True,
    }

    for path in paths:
        assert is_runtime_artifact_path(path)
        assert classify_worktree_path_area(path) == "runtime_artifact"
    assert has_cleanup_artifact_pressure(live_signals)
    assert not has_commit_isolation_worktree_pressure(live_signals)


def test_root_tmp_scratch_is_runtime_artifact_pressure() -> None:
    paths = [
        "tmp_mypy_smoke.py",
        "tmp_mypy_cache/3.10/cache.db",
        "tmp_rmtree_probe/x.txt",
    ]
    live_signals = {
        "modified_paths": [],
        "untracked_paths": paths,
        "runtime_artifact_paths": paths,
        "benchmark_result_paths": [],
        "generated_artifact_policy_explicit": True,
    }

    for path in paths:
        assert is_runtime_artifact_path(path)
        assert classify_worktree_path_area(path) == "runtime_artifact"
    assert has_cleanup_artifact_pressure(live_signals)
    assert not has_commit_isolation_worktree_pressure(live_signals)


def test_benchmark_minlock_probe_is_runtime_artifact_pressure() -> None:
    paths = [
        "benchmarks/minlock-plain.txt",
        "benchmarks/minlock-repro/.benchmark.lock",
        "benchmarks/minlock-x.txt",
    ]
    live_signals = {
        "modified_paths": [],
        "untracked_paths": paths,
        "runtime_artifact_paths": paths,
        "benchmark_result_paths": [],
        "generated_artifact_policy_explicit": True,
    }

    for path in paths:
        assert is_runtime_artifact_path(path)
        assert classify_worktree_path_area(path) == "runtime_artifact"
    assert has_cleanup_artifact_pressure(live_signals)
    assert not has_commit_isolation_worktree_pressure(live_signals)


def test_mypy_ini_is_config_area_not_other() -> None:
    assert classify_worktree_path_area("mypy.ini") == "config"
