"""Lifecycle and backlog-closure tests for QA-Z self-improvement."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.self_improvement import compact_backlog_evidence_summary, run_self_inspection
from tests.self_improvement_test_support import (
    assert_mapping_contains,
    stub_live_repository_signals,
    write_aggregate_only_failed_benchmark_summary,
    write_benchmark_summary,
    write_fixture_index,
    write_incomplete_session,
    write_json,
    write_legacy_benchmark_summary_without_snapshot,
    write_regressed_verify_summary,
    write_report,
)


NOW = "2026-04-15T00:00:00Z"


def test_self_inspection_writes_report_and_updates_backlog(tmp_path: Path) -> None:
    write_benchmark_summary(tmp_path)
    write_regressed_verify_summary(tmp_path)
    write_incomplete_session(tmp_path)
    write_fixture_index(tmp_path, ["py_type_error"])

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="loop-one")

    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))

    assert paths.self_inspection_path == (
        tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json"
    )
    assert report["kind"] == "qa_z.self_inspection"
    assert report["loop_id"] == "loop-one"
    assert_mapping_contains(
        report["live_repository"],
        {
            "benchmark_result_count": 1,
            "dirty_benchmark_result_count": 0,
            "current_branch": None,
            "current_head": None,
            "dirty_area_summary": "",
            "generated_artifact_policy_explicit": False,
            "modified_count": 0,
            "release_evidence_count": 0,
            "runtime_artifact_count": 0,
            "staged_count": 0,
            "untracked_count": 0,
        },
    )
    assert {
        "benchmark_gap",
        "verify_regression",
        "session_gap",
        "coverage_gap",
    } <= {candidate["category"] for candidate in report["candidates"]}
    assert backlog["kind"] == "qa_z.improvement_backlog"
    assert backlog["updated_at"] == NOW
    assert all(item["status"] == "open" for item in backlog["items"])
    assert all(item["evidence"] for item in backlog["items"])
    assert all(isinstance(item["priority_score"], int) for item in backlog["items"])
    benchmark_item = next(
        item for item in backlog["items"] if item["id"] == "benchmark_gap-py_type_error"
    )
    assert (
        "snapshot=1/2 fixtures, overall_rate 0.5"
        in (benchmark_item["evidence"][0]["summary"])
    )
    assert compact_backlog_evidence_summary(benchmark_item).startswith(
        "benchmark: snapshot=1/2 fixtures, overall_rate 0.5; fixture=py_type_error"
    )


def test_self_inspection_report_records_live_repository_snapshot(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=2,
        untracked_count=1,
        staged_count=1,
        modified_paths=["README.md", "src/qa_z/self_improvement.py"],
        untracked_paths=[".qa-z/loops/latest/outcome.json"],
        runtime_artifact_paths=[".qa-z/loops/latest/outcome.json"],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
        generated_artifact_policy_explicit=True,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="live-snapshot")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    assert_mapping_contains(
        report["live_repository"],
        {
            "benchmark_result_count": 2,
            "dirty_benchmark_result_count": 0,
            "current_branch": None,
            "current_head": None,
            "dirty_area_summary": "docs:1, runtime_artifact:1, source:1",
            "generated_artifact_policy_explicit": True,
            "modified_count": 2,
            "release_evidence_count": 0,
            "runtime_artifact_count": 1,
            "staged_count": 1,
            "untracked_count": 1,
        },
    )


def test_self_inspection_synthesizes_snapshot_for_legacy_benchmark_summary(
    tmp_path: Path,
) -> None:
    write_legacy_benchmark_summary_without_snapshot(tmp_path)
    write_fixture_index(tmp_path, ["py_type_error"])

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="legacy-benchmark-loop")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    benchmark_item = next(
        item for item in backlog["items"] if item["id"] == "benchmark_gap-py_type_error"
    )

    assert (
        "snapshot=1/2 fixtures, overall_rate 0.5"
        in (benchmark_item["evidence"][0]["summary"])
    )


def test_self_inspection_creates_summary_candidate_for_aggregate_benchmark_failure(
    tmp_path: Path,
) -> None:
    write_aggregate_only_failed_benchmark_summary(tmp_path)

    paths = run_self_inspection(
        root=tmp_path, now=NOW, loop_id="aggregate-benchmark-loop"
    )
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    benchmark_item = next(
        item for item in backlog["items"] if item["id"] == "benchmark_gap-summary"
    )

    assert (
        "snapshot=1/2 fixtures, overall_rate 0.5"
        in (benchmark_item["evidence"][0]["summary"])
    )
    assert (
        "benchmark summary reports 1 failed fixture without fixture details"
        in (benchmark_item["evidence"][0]["summary"])
    )


def test_self_inspection_preserves_recurrence_from_existing_backlog(
    tmp_path: Path,
) -> None:
    write_benchmark_summary(tmp_path)
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-14T00:00:00Z",
            "items": [
                {
                    "id": "benchmark_gap-py_type_error",
                    "title": "Fix benchmark fixture failure: py_type_error",
                    "category": "benchmark_gap",
                    "evidence": [{"source": "benchmark"}],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 62,
                    "status": "open",
                    "recommendation": "add_benchmark_fixture",
                    "signals": ["benchmark_fail"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                }
            ],
        },
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="loop-two")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    benchmark_item = next(
        item for item in backlog["items"] if item["id"] == "benchmark_gap-py_type_error"
    )

    assert benchmark_item["first_seen_at"] == "2026-04-14T00:00:00Z"
    assert benchmark_item["last_seen_at"] == NOW
    assert benchmark_item["recurrence_count"] == 2
    assert benchmark_item["priority_score"] == 63


def test_self_inspection_with_no_evidence_writes_empty_artifacts(
    tmp_path: Path,
) -> None:
    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="empty-loop")

    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))

    assert report["candidates"] == []
    assert report["evidence_sources"] == []
    assert backlog["items"] == []


def test_self_inspection_closes_stale_open_backlog_items_not_reobserved(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-14T00:00:00Z",
            "items": [
                {
                    "id": "artifact_hygiene_gap-runtime-source-separation",
                    "title": "Separate runtime artifacts from source-tracked evidence",
                    "category": "artifact_hygiene_gap",
                    "evidence": [
                        {
                            "source": "roadmap",
                            "path": "docs/reports/next-improvement-roadmap.md",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 63,
                    "status": "open",
                    "recommendation": "separate_runtime_from_source_artifacts",
                    "signals": ["generated_artifact_policy_ambiguity"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                }
            ],
        },
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="close-stale-loop")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    item = backlog["items"][0]

    assert item["status"] == "closed"
    assert item["closed_at"] == NOW
    assert item["closure_reason"] == "not_observed_in_latest_inspection"
    assert item["last_seen_at"] == "2026-04-14T00:00:00Z"


def test_self_inspection_closes_cleanup_backlog_items_with_freshness_guard_reason(
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
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-14T00:00:00Z",
            "items": [
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 63,
                    "status": "open",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                },
                {
                    "id": "integration_gap-worktree-integration-risk",
                    "title": "Audit worktree integration and commit-split risk",
                    "category": "integration_gap",
                    "evidence": [
                        {
                            "source": "worktree_triage",
                            "path": "docs/reports/worktree-triage.md",
                        }
                    ],
                    "impact": 2,
                    "likelihood": 3,
                    "confidence": 4,
                    "repair_cost": 2,
                    "priority_score": 57,
                    "status": "open",
                    "recommendation": "audit_worktree_integration",
                    "signals": ["worktree_integration_risk"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                },
            ],
        },
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

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="freshness-close")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    closed = {item["id"]: item for item in backlog["items"]}

    assert closed["commit_isolation_gap-foundation-order"]["status"] == "closed"
    assert (
        closed["commit_isolation_gap-foundation-order"]["closure_reason"]
        == "freshness_guard_not_satisfied"
    )
    assert closed["integration_gap-worktree-integration-risk"]["status"] == "closed"
    assert (
        closed["integration_gap-worktree-integration-risk"]["closure_reason"]
        == "freshness_guard_not_satisfied"
    )


def test_self_inspection_closes_headless_cleanup_items_when_live_head_is_known(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=2,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["benchmarks/results/report.md"],
        runtime_artifact_paths=["benchmarks/results/report.md"],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-14T00:00:00Z",
            "items": [
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 63,
                    "status": "open",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                },
                {
                    "id": "deferred_cleanup_gap-worktree-deferred-items",
                    "title": "Triage deferred cleanup items before they drift further",
                    "category": "deferred_cleanup_gap",
                    "evidence": [
                        {
                            "source": "current_state",
                            "path": "docs/reports/current-state-analysis.md",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 63,
                    "status": "open",
                    "recommendation": "triage_and_isolate_changes",
                    "signals": ["deferred_cleanup_repeated"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                },
            ],
        },
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-15
        Branch context: `codex/qa-z-bootstrap`

        Deferred cleanup once mentioned generated benchmark outputs and
        intentionally frozen evidence decisions.
        """,
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation and `git add -p`.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="headless-close")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    closed = {item["id"]: item for item in backlog["items"]}

    assert closed["commit_isolation_gap-foundation-order"]["status"] == "closed"
    assert (
        closed["commit_isolation_gap-foundation-order"]["closure_reason"]
        == "freshness_guard_not_satisfied"
    )
    assert closed["deferred_cleanup_gap-worktree-deferred-items"]["status"] == "closed"
    assert (
        closed["deferred_cleanup_gap-worktree-deferred-items"]["closure_reason"]
        == "freshness_guard_not_satisfied"
    )


def test_self_inspection_keeps_in_progress_backlog_items_when_not_reobserved(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-14T00:00:00Z",
            "items": [
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 63,
                    "status": "in_progress",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                }
            ],
        },
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="keep-progress-loop")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    item = backlog["items"][0]

    assert item["status"] == "in_progress"
    assert "closed_at" not in item
    assert "closure_reason" not in item
