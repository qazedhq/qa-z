"""Tests for loop-health self-improvement signal inputs."""

from __future__ import annotations

from pathlib import Path

import qa_z.loop_health_signals as loop_health_signals_module
from tests.self_improvement_test_support import write_json, write_loop_history


NOW = "2026-04-15T00:00:00Z"


def test_discover_empty_loop_candidate_inputs_uses_recent_history_chain(
    tmp_path: Path,
) -> None:
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": NOW,
                "selected_tasks": [],
                "next_candidates": [],
                "state": "blocked_no_candidates",
                "loop_elapsed_seconds": 1,
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": NOW,
                "selected_tasks": [],
                "next_candidates": [],
                "state": "blocked_no_candidates",
                "loop_elapsed_seconds": 1,
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-3",
                "created_at": NOW,
                "selected_tasks": [],
                "next_candidates": [],
                "state": "fallback_selected",
                "loop_elapsed_seconds": 1,
            },
        ],
    )

    candidates = loop_health_signals_module.discover_empty_loop_candidate_inputs(
        tmp_path
    )

    assert candidates == [
        {
            "id": "autonomy_selection_gap-empty-loop-chain",
            "title": "Prevent repeated empty autonomy selection loops",
            "category": "autonomy_selection_gap",
            "evidence": [
                {
                    "source": "loop_history",
                    "path": tmp_path / ".qa-z" / "loops" / "history.jsonl",
                    "summary": (
                        "recent_empty_loops=3; loop_ids=loop-1, loop-2, loop-3; "
                        "states=blocked_no_candidates, blocked_no_candidates, "
                        "fallback_selected"
                    ),
                }
            ],
            "impact": 4,
            "likelihood": 4,
            "confidence": 4,
            "repair_cost": 2,
            "recommendation": "improve_empty_loop_handling",
            "signals": ["recent_empty_loop_chain", "service_readiness_gap"],
        }
    ]


def test_discover_empty_loop_candidate_inputs_ignores_selection_refresh_gaps(
    tmp_path: Path,
) -> None:
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": NOW,
                "selected_tasks": [],
                "next_candidates": [],
                "state": "blocked_no_candidates",
                "selection_gap_reason": "no_open_backlog_after_inspection",
                "open_backlog_count": 0,
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": NOW,
                "selected_tasks": [],
                "next_candidates": [],
                "state": "blocked_no_candidates",
                "selection_gap_reason": "no_open_backlog_after_inspection",
                "open_backlog_count": 0,
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-3",
                "created_at": NOW,
                "selected_tasks": [],
                "next_candidates": [],
                "state": "blocked_no_candidates",
                "selection_gap_reason": "no_open_backlog_after_inspection",
                "open_backlog_count": 0,
            },
        ],
    )

    assert (
        loop_health_signals_module.discover_empty_loop_candidate_inputs(tmp_path) == []
    )


def test_discover_repeated_fallback_family_inputs_use_autonomy_outcomes(
    tmp_path: Path,
) -> None:
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": NOW,
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "selected_fallback_families": ["cleanup"],
                "state": "fallback_selected",
                "loop_elapsed_seconds": 1,
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": NOW,
                "selected_tasks": ["commit_isolation_gap-foundation-order"],
                "selected_fallback_families": ["cleanup"],
                "state": "fallback_selected",
                "loop_elapsed_seconds": 1,
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-3",
                "created_at": NOW,
                "selected_tasks": ["evidence_freshness_gap-generated-artifacts"],
                "selected_fallback_families": ["cleanup"],
                "state": "fallback_selected",
                "loop_elapsed_seconds": 1,
            },
        ],
    )

    candidates = (
        loop_health_signals_module.discover_repeated_fallback_family_candidate_inputs(
            tmp_path
        )
    )

    assert candidates[0]["id"] == "autonomy_selection_gap-repeated-fallback-cleanup"
    assert candidates[0]["recommendation"] == "improve_fallback_diversity"
    assert "states=fallback_selected, fallback_selected, fallback_selected" in str(
        candidates[0]["evidence"][0]["summary"]
    )


def test_discover_repeated_fallback_family_inputs_ignore_selection_refresh_history(
    tmp_path: Path,
) -> None:
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": NOW,
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "selected_fallback_families": ["cleanup"],
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": NOW,
                "selected_tasks": ["commit_isolation_gap-foundation-order"],
                "selected_fallback_families": ["cleanup"],
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-3",
                "created_at": NOW,
                "selected_tasks": ["evidence_freshness_gap-generated-artifacts"],
                "selected_fallback_families": ["cleanup"],
            },
        ],
    )

    assert (
        loop_health_signals_module.discover_repeated_fallback_family_candidate_inputs(
            tmp_path
        )
        == []
    )


def test_discover_repeated_fallback_family_inputs_require_recent_autonomy_window(
    tmp_path: Path,
) -> None:
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": NOW,
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "selected_fallback_families": ["cleanup"],
                "state": "fallback_selected",
                "loop_elapsed_seconds": 1,
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": NOW,
                "selected_tasks": ["commit_isolation_gap-foundation-order"],
                "selected_fallback_families": ["cleanup"],
                "state": "fallback_selected",
                "loop_elapsed_seconds": 1,
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-3",
                "created_at": NOW,
                "selected_tasks": ["verify_regression-resolved"],
                "state": "completed",
                "loop_elapsed_seconds": 1,
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-4",
                "created_at": NOW,
                "selected_tasks": ["artifact_hygiene_gap-runtime"],
                "selected_fallback_families": ["cleanup"],
                "state": "fallback_selected",
                "loop_elapsed_seconds": 1,
            },
        ],
    )

    assert (
        loop_health_signals_module.discover_repeated_fallback_family_candidate_inputs(
            tmp_path
        )
        == []
    )


def test_latest_self_inspection_selection_context_reads_loop_local_provenance(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json",
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "loop-42",
            "generated_at": NOW,
            "live_repository": {"modified_count": 2},
        },
    )

    context = loop_health_signals_module.latest_self_inspection_selection_context(
        tmp_path
    )

    assert context == {
        "source_self_inspection": ".qa-z/loops/latest/self_inspect.json",
        "live_repository": {"modified_count": 2},
        "source_self_inspection_loop_id": "loop-42",
        "source_self_inspection_generated_at": NOW,
    }
