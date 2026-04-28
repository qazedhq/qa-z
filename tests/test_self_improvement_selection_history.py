"""Tests for self-improvement selection history and fallback diversity."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.self_improvement import (
    BacklogCandidate,
    run_self_inspection,
    score_candidate,
    select_next_tasks,
)
from tests.self_improvement_test_support import write_json, write_loop_history


NOW = "2026-04-15T00:00:00Z"


def test_score_candidate_prioritizes_worktree_risk_over_docs_drift() -> None:
    worktree_candidate = BacklogCandidate(
        id="worktree_risk-dirty-worktree",
        title="Reduce dirty worktree integration risk",
        category="worktree_risk",
        evidence=[
            {
                "source": "git_status",
                "path": ".",
                "summary": "modified=12; untracked=24; staged=0",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=4,
        repair_cost=3,
        recommendation="reduce_integration_risk",
        signals=["dirty_worktree_large", "worktree_integration_risk"],
    )
    docs_candidate = BacklogCandidate(
        id="docs_drift-current_truth_sync",
        title="Run a current-truth docs and schema sync audit",
        category="docs_drift",
        evidence=[
            {
                "source": "docs",
                "path": "README.md",
                "summary": "command surface drift",
            }
        ],
        impact=2,
        likelihood=3,
        confidence=4,
        repair_cost=2,
        recommendation="sync_contract_and_docs",
        signals=["schema_doc_drift"],
    )

    assert score_candidate(worktree_candidate) > score_candidate(docs_candidate)


def test_score_candidate_prioritizes_explicit_runtime_cleanup_over_hygiene() -> None:
    cleanup_candidate = BacklogCandidate(
        id="runtime_artifact_cleanup_gap-generated-results",
        title="Clean up generated runtime artifacts before source integration",
        category="runtime_artifact_cleanup_gap",
        evidence=[
            {
                "source": "runtime_artifacts",
                "path": "benchmarks/results-analysis/report.md",
                "summary": "generated runtime artifacts need explicit cleanup handling",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=4,
        repair_cost=3,
        recommendation="triage_and_isolate_changes",
        signals=["worktree_integration_risk", "policy_managed_runtime_artifacts"],
    )
    hygiene_candidate = BacklogCandidate(
        id="artifact_hygiene_gap-runtime-source-separation",
        title="Separate runtime artifacts from source-tracked evidence",
        category="artifact_hygiene_gap",
        evidence=[
            {
                "source": "runtime_artifacts",
                "path": "benchmarks/results-analysis/report.md",
                "summary": "runtime artifacts are still mixed into the worktree",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=4,
        repair_cost=3,
        recommendation="separate_runtime_from_source_artifacts",
        signals=["worktree_integration_risk", "runtime_artifact_source_mixing"],
    )

    assert score_candidate(cleanup_candidate) > score_candidate(hygiene_candidate)


def test_select_next_penalizes_recent_reselection_from_loop_history(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 61,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 2,
                },
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                            "summary": "commit order dependency remains",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 60,
                    "status": "open",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": "2026-04-14T00:00:00Z",
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "evidence_used": ["."],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": ["commit_isolation_gap-foundation-order"],
                "state": "fallback_selected",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": "2026-04-14T00:05:00Z",
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "evidence_used": ["."],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": ["commit_isolation_gap-foundation-order"],
                "state": "fallback_selected",
            },
        ],
    )

    paths = select_next_tasks(root=tmp_path, count=1, now=NOW, loop_id="penalty-loop")
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "commit_isolation_gap-foundation-order"
    ]
    assert selected["selected_tasks"][0]["selection_penalty"] == 0


def test_select_next_penalizes_repeated_fallback_family_when_alternative_exists(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 62,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 2,
                },
                {
                    "id": "coverage_gap-mixed-surface-benchmark-realism",
                    "title": "Expand executed mixed-surface benchmark realism",
                    "category": "coverage_gap",
                    "evidence": [
                        {
                            "source": "roadmap",
                            "path": "docs/reports/next-improvement-roadmap.md",
                            "summary": "mixed-surface executed benchmark expansion remains open",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 61,
                    "status": "open",
                    "recommendation": "add_benchmark_fixture",
                    "signals": ["mixed_surface_realism_gap"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": "2026-04-14T00:00:00Z",
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "selected_categories": ["worktree_risk"],
                "evidence_used": ["."],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": ["coverage_gap-mixed-surface-benchmark-realism"],
                "state": "fallback_selected",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": "2026-04-14T00:05:00Z",
                "selected_tasks": ["commit_isolation_gap-foundation-order"],
                "selected_categories": ["commit_isolation_gap"],
                "evidence_used": ["docs/reports/worktree-commit-plan.md"],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": ["coverage_gap-mixed-surface-benchmark-realism"],
                "state": "fallback_selected",
            },
        ],
    )

    paths = select_next_tasks(root=tmp_path, count=1, now=NOW, loop_id="family-penalty")
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    history = json.loads(
        paths.history_path.read_text(encoding="utf-8").splitlines()[-1]
    )

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "coverage_gap-mixed-surface-benchmark-realism"
    ]
    assert selected["selected_tasks"][0]["selection_penalty"] == 0
    assert history["selected_fallback_families"] == ["benchmark_expansion"]
    assert "worktree_risk-dirty-worktree" in history["next_candidates"]


def test_select_next_diversifies_fallback_families_within_one_batch(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 62,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                            "summary": "commit order dependency remains",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 61,
                    "status": "open",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
                {
                    "id": "coverage_gap-mixed-surface-benchmark-realism",
                    "title": "Expand executed mixed-surface benchmark realism",
                    "category": "coverage_gap",
                    "evidence": [
                        {
                            "source": "roadmap",
                            "path": "docs/reports/next-improvement-roadmap.md",
                            "summary": "mixed-surface expansion remains open",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 60,
                    "status": "open",
                    "recommendation": "add_benchmark_fixture",
                    "signals": ["mixed_surface_realism_gap"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )

    paths = select_next_tasks(
        root=tmp_path, count=2, now=NOW, loop_id="batch-diversity"
    )
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    history = json.loads(
        paths.history_path.read_text(encoding="utf-8").splitlines()[-1]
    )

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "worktree_risk-dirty-worktree",
        "coverage_gap-mixed-surface-benchmark-realism",
    ]
    assert history["selected_fallback_families"] == ["benchmark_expansion", "cleanup"]
    assert "commit_isolation_gap-foundation-order" in history["next_candidates"]


def test_select_next_surfaces_non_repeated_family_after_fallback_diversity_task(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "autonomy_selection_gap-repeated-fallback-cleanup",
                    "title": "Diversify repeated fallback selections across task families",
                    "category": "autonomy_selection_gap",
                    "evidence": [
                        {
                            "source": "loop_history",
                            "path": ".qa-z/loops/history.jsonl",
                            "summary": "recent_fallback_family=cleanup; loops=3",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 2,
                    "priority_score": 67,
                    "status": "open",
                    "recommendation": "improve_fallback_diversity",
                    "signals": ["recent_fallback_family_repeat"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 3,
                },
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 65,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 2,
                },
                {
                    "id": "artifact_hygiene_gap-runtime-source-separation",
                    "title": "Separate runtime artifacts from source-tracked evidence",
                    "category": "artifact_hygiene_gap",
                    "evidence": [
                        {
                            "source": "runtime_artifacts",
                            "path": "benchmarks/results/report.md",
                            "summary": "runtime artifacts are mixed into the worktree",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 64,
                    "status": "open",
                    "recommendation": "separate_runtime_from_source_artifacts",
                    "signals": ["generated_artifact_policy_ambiguity"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 2,
                },
                {
                    "id": "integration_gap-worktree-integration-risk",
                    "title": "Audit worktree integration and commit-split risk",
                    "category": "integration_gap",
                    "evidence": [
                        {
                            "source": "current_state",
                            "path": "docs/reports/current-state-analysis.md",
                            "summary": "integration worktree still spans multiple surfaces",
                        }
                    ],
                    "impact": 2,
                    "likelihood": 3,
                    "confidence": 4,
                    "repair_cost": 2,
                    "priority_score": 23,
                    "status": "open",
                    "recommendation": "audit_worktree_integration",
                    "signals": ["worktree_integration_risk"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )

    paths = select_next_tasks(root=tmp_path, count=3, now=NOW, loop_id="family-balance")
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "integration_gap-worktree-integration-risk",
        "autonomy_selection_gap-repeated-fallback-cleanup",
        "worktree_risk-dirty-worktree",
    ]


def test_select_next_keeps_cleanup_family_when_no_alternative_family_exists(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "autonomy_selection_gap-repeated-fallback-cleanup",
                    "title": "Diversify repeated fallback selections across task families",
                    "category": "autonomy_selection_gap",
                    "evidence": [
                        {
                            "source": "loop_history",
                            "path": ".qa-z/loops/history.jsonl",
                            "summary": "recent_fallback_family=cleanup; loops=3",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 2,
                    "priority_score": 67,
                    "status": "open",
                    "recommendation": "improve_fallback_diversity",
                    "signals": ["recent_fallback_family_repeat"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 3,
                },
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 65,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 2,
                },
                {
                    "id": "artifact_hygiene_gap-runtime-source-separation",
                    "title": "Separate runtime artifacts from source-tracked evidence",
                    "category": "artifact_hygiene_gap",
                    "evidence": [
                        {
                            "source": "runtime_artifacts",
                            "path": "benchmarks/results/report.md",
                            "summary": "runtime artifacts are mixed into the worktree",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 64,
                    "status": "open",
                    "recommendation": "separate_runtime_from_source_artifacts",
                    "signals": ["generated_artifact_policy_ambiguity"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 2,
                },
            ],
        },
    )

    paths = select_next_tasks(
        root=tmp_path, count=2, now=NOW, loop_id="family-fallback"
    )
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "autonomy_selection_gap-repeated-fallback-cleanup",
        "worktree_risk-dirty-worktree",
    ]


def test_select_next_keeps_same_fallback_family_when_no_alternative_exists(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 62,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                            "summary": "commit order dependency remains",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 61,
                    "status": "open",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )

    paths = select_next_tasks(
        root=tmp_path, count=2, now=NOW, loop_id="batch-same-family"
    )
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "worktree_risk-dirty-worktree",
        "commit_isolation_gap-foundation-order",
    ]


def test_self_inspection_derives_autonomy_selection_gap_from_repeated_fallback_family(
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
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "selected_categories": ["worktree_risk"],
                "selected_fallback_families": ["cleanup"],
                "evidence_used": ["."],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "fallback_selected",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": "2026-04-14T00:05:00Z",
                "selected_tasks": ["commit_isolation_gap-foundation-order"],
                "selected_categories": ["commit_isolation_gap"],
                "selected_fallback_families": ["cleanup"],
                "evidence_used": ["docs/reports/worktree-commit-plan.md"],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "fallback_selected",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-3",
                "created_at": "2026-04-14T00:10:00Z",
                "selected_tasks": ["evidence_freshness_gap-generated-artifacts"],
                "selected_categories": ["evidence_freshness_gap"],
                "selected_fallback_families": ["cleanup"],
                "evidence_used": ["benchmarks/results/summary.json"],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "fallback_selected",
            },
        ],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="family-history-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    candidate = next(
        item
        for item in report["candidates"]
        if item["id"] == "autonomy_selection_gap-repeated-fallback-cleanup"
    )

    assert candidate["category"] == "autonomy_selection_gap"
    assert candidate["recommendation"] == "improve_fallback_diversity"
    assert "recent_fallback_family_repeat" in candidate["signals"]
    assert "loop_ids=loop-1, loop-2, loop-3" in candidate["evidence"][0]["summary"]
