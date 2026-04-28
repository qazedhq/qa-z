"""Reseeding and policy-signal tests for self-improvement."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.self_improvement import (
    classify_worktree_path_area,
    is_runtime_artifact_path,
    run_self_inspection,
    select_next_tasks,
)
from tests.self_improvement_test_support import (
    stub_live_repository_signals,
    write_loop_history,
    write_report,
)


NOW = "2026-04-15T00:00:00Z"


def test_self_inspection_reseeds_backlog_from_reports_when_empty(
    tmp_path: Path,
) -> None:
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        ## Known Gaps

        ### Mixed-Surface Executed Benchmark Expansion

        Mixed-language verification coverage exists, but executed mixed-surface
        behavior across fast, deep, and repair handoff is still thin.

        ### Current-Truth Drift Risk

        README, artifact schema, config example, and CLI behavior still need a
        current-truth audit.
        """,
    )
    write_report(
        tmp_path,
        "next-improvement-roadmap.md",
        """
        # QA-Z Next Improvement Roadmap

        ## Priority 3: Mixed-Surface Executed Benchmark Expansion

        Add realistic mixed-surface fixtures that exercise fast, deep, and
        handoff behavior.

        ## Priority 4: Current-Truth Sync Audit

        Run one explicit sync audit across README, schema docs, config example,
        and CLI behavior.
        """,
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        README.md and docs/artifact-schema-v1.md should stay in sync with the
        current command surface before the alpha baseline hardens.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="report-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))

    assert report["loop_id"] == "report-loop"
    assert {
        "coverage_gap",
        "docs_drift",
        "backlog_reseeding_gap",
    } <= {candidate["category"] for candidate in report["candidates"]}
    assert report["backlog_reseeded"] is True
    assert set(report["reseeded_candidate_ids"]) == {
        candidate["id"]
        for candidate in report["candidates"]
        if candidate["category"] != "backlog_reseeding_gap"
    }
    assert any(
        entry["source"] == "roadmap"
        for candidate in report["candidates"]
        for entry in candidate["evidence"]
    )
    assert any(
        entry["source"] == "current_state"
        for candidate in report["candidates"]
        for entry in candidate["evidence"]
    )
    assert {item["category"] for item in backlog["items"]} == {
        "coverage_gap",
        "docs_drift",
    }


def test_select_next_keeps_reseeded_backlog_concrete_when_meta_signal_exists(
    tmp_path: Path,
) -> None:
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        ## Known Gaps

        ### Mixed-Surface Executed Benchmark Expansion

        Mixed-language verification coverage exists, but executed mixed-surface
        behavior across fast, deep, and repair handoff is still thin.

        ### Current-Truth Drift Risk

        README, artifact schema, config example, and CLI behavior still need a
        current-truth audit.
        """,
    )
    write_report(
        tmp_path,
        "next-improvement-roadmap.md",
        """
        # QA-Z Next Improvement Roadmap

        ## Priority 3: Mixed-Surface Executed Benchmark Expansion

        Add realistic mixed-surface fixtures that exercise fast, deep, and
        handoff behavior.

        ## Priority 4: Current-Truth Sync Audit

        Run one explicit sync audit across README, schema docs, config example,
        and CLI behavior.
        """,
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        README.md and docs/artifact-schema-v1.md should stay in sync with the
        current command surface before the alpha baseline hardens.
        """,
    )

    run_self_inspection(root=tmp_path, now=NOW, loop_id="report-loop")
    paths = select_next_tasks(
        root=tmp_path,
        count=3,
        now=NOW,
        loop_id="selection-loop",
    )
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))

    assert len(selected["selected_tasks"]) == 2
    assert {item["category"] for item in selected["selected_tasks"]} == {
        "coverage_gap",
        "docs_drift",
    }
    assert all(
        item["category"] != "backlog_reseeding_gap"
        for item in selected["selected_tasks"]
    )


def test_self_inspection_skips_cleanup_classes_for_docs_only_current_truth_churn(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=3,
        untracked_count=2,
        staged_count=0,
        modified_paths=[
            "README.md",
            "docs/reports/current-state-analysis.md",
            "docs/reports/next-improvement-roadmap.md",
        ],
        untracked_paths=["tests/test_current_truth.py", "tests/test_cli.py"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-15
        Branch context: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

        README, artifact schema, config example, and CLI behavior still need a
        current-truth audit.
        """,
    )
    write_report(
        tmp_path,
        "next-improvement-roadmap.md",
        """
        # QA-Z Next Improvement Roadmap

        Date: 2026-04-15
        Branch context: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

        Run one explicit sync audit across README, schema docs, config example,
        and CLI behavior.
        """,
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

        Dirty worktree integration caveats need a commit split before release.
        """,
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation and `git add -p`.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="docs-only-churn")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {candidate["category"] for candidate in report["candidates"]}

    assert "docs_drift" in categories
    assert "commit_isolation_gap" not in categories
    assert "integration_gap" not in categories
    assert "deferred_cleanup_gap" not in categories


def test_self_inspection_derives_autonomy_selection_gap_from_empty_loop_history(
    tmp_path: Path,
) -> None:
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": "2026-04-14T00:00:00Z",
                "selected_tasks": [],
                "evidence_used": [],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "blocked_no_candidates",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": "2026-04-14T00:05:00Z",
                "selected_tasks": [],
                "evidence_used": [],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "blocked_no_candidates",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-3",
                "created_at": "2026-04-14T00:10:00Z",
                "selected_tasks": [],
                "evidence_used": [],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "blocked_no_candidates",
            },
        ],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="history-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    candidate = next(
        item
        for item in report["candidates"]
        if item["category"] == "autonomy_selection_gap"
    )

    assert candidate["id"] == "autonomy_selection_gap-empty-loop-chain"
    assert "recent_empty_loop_chain" in candidate["signals"]
    assert candidate["recommendation"] == "improve_empty_loop_handling"


def test_self_inspection_promotes_dirty_worktree_risk_from_live_signals(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=12,
        untracked_count=24,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["docs/reports/worktree-triage.md", "src/qa_z/autonomy.py"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="worktree-risk-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    candidate = next(
        item for item in report["candidates"] if item["category"] == "worktree_risk"
    )

    assert candidate["id"] == "worktree_risk-dirty-worktree"
    assert candidate["recommendation"] == "reduce_integration_risk"
    assert "dirty_worktree_large" in candidate["signals"]
    assert "modified=12" in candidate["evidence"][0]["summary"]
    assert "untracked=24" in candidate["evidence"][0]["summary"]
    assert "areas=docs:2, source:2" in candidate["evidence"][0]["summary"]


def test_runtime_artifact_path_detects_benchmark_snapshot_siblings() -> None:
    assert is_runtime_artifact_path("benchmarks/results/report.md") is True
    assert is_runtime_artifact_path("benchmarks/results-p12-dry-run/report.md") is True
    assert (
        is_runtime_artifact_path("benchmarks/results-p12-dry-run/work/run.json") is True
    )
    assert (
        is_runtime_artifact_path("benchmarks/fixtures/py_test_failure/expected.json")
        is False
    )


def test_worktree_area_classifies_benchmark_snapshots_as_benchmark_evidence() -> None:
    assert (
        classify_worktree_path_area("benchmarks/results-p12-dry-run/report.md")
        == "benchmark"
    )
    assert (
        classify_worktree_path_area("benchmarks/fixtures/py_test_failure/expected.json")
        == "benchmark"
    )
