"""Tests for self-improvement export and seam surfaces."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.backlog_core as backlog_core_module
import qa_z.backlog_reseeding_signals as backlog_reseeding_signals_module
import qa_z.benchmark_signal_artifacts as benchmark_signal_artifacts_module
import qa_z.benchmark_signals as benchmark_signals_module
import qa_z.discovery_pipeline as discovery_pipeline_module
import qa_z.docs_surface_discovery as docs_surface_discovery_module
import qa_z.coverage_gap_discovery as coverage_gap_discovery_module
import qa_z.executor_history_summary as executor_history_summary_module
import qa_z.executor_history_signals as executor_history_signals_module
import qa_z.executor_history_records as executor_history_records_module
import qa_z.executor_signals as executor_signals_module
import qa_z.execution_discovery as execution_discovery_module
import qa_z.git_runtime as git_runtime_module
import qa_z.improvement_state as improvement_state_module
import qa_z.live_repository as live_repository_module
import qa_z.loop_health_signals as loop_health_signals_module
import qa_z.loop_history_candidates as loop_history_candidates_module
import qa_z.report_signals as report_signals_module
import qa_z.repair_signals as repair_signals_module
import qa_z.selection_context as selection_context_module
import qa_z.self_improvement as self_improvement_module
import qa_z.surface_discovery as surface_discovery_module
import qa_z.task_selection as task_selection_module
import qa_z.worktree_discovery as worktree_discovery_module
import qa_z.artifact_consistency_discovery as artifact_consistency_discovery_module
import qa_z.self_improvement_stage_groups as self_improvement_stage_groups_module
from qa_z.self_improvement import (
    BacklogCandidate,
    benchmark_summary_snapshot,
    collect_live_repository_signals,
    discover_artifact_consistency_candidates,
    discover_commit_isolation_candidates,
    discover_coverage_gap_candidates,
    discover_docs_drift_candidates,
    discover_executor_contract_candidates,
    discover_executor_history_candidates,
    discover_executor_ingest_candidates,
    discover_executor_result_candidates,
    discover_integration_gap_candidates,
    discover_session_candidates,
    discover_verification_candidates,
    fallback_family_for_category,
    load_backlog,
    open_backlog_items,
    render_live_repository_summary,
    render_loop_plan,
    score_candidate,
)


def test_live_repository_module_exports_match_self_improvement_surface() -> None:
    assert (
        live_repository_module.collect_live_repository_signals
        is collect_live_repository_signals
    )
    assert (
        live_repository_module.render_live_repository_summary
        is render_live_repository_summary
    )


def test_benchmark_signals_module_exports_match_self_improvement_surface() -> None:
    assert (
        benchmark_signals_module.benchmark_summary_snapshot
        is benchmark_summary_snapshot
    )


def test_backlog_core_module_exports_match_self_improvement_surface() -> None:
    assert backlog_core_module.BacklogCandidate is BacklogCandidate
    assert backlog_core_module.score_candidate is score_candidate


def test_task_selection_module_exports_match_self_improvement_surface() -> None:
    assert (
        task_selection_module.fallback_family_for_category
        is fallback_family_for_category
    )
    assert task_selection_module.render_loop_plan is render_loop_plan


def test_worktree_discovery_module_exports_match_self_improvement_surface() -> None:
    assert (
        worktree_discovery_module.discover_commit_isolation_candidates
        is discover_commit_isolation_candidates
    )
    assert (
        worktree_discovery_module.discover_integration_gap_candidates
        is discover_integration_gap_candidates
    )


def test_execution_discovery_module_exports_match_self_improvement_surface() -> None:
    assert (
        execution_discovery_module.discover_verification_candidates
        is discover_verification_candidates
    )
    assert (
        execution_discovery_module.discover_session_candidates
        is discover_session_candidates
    )
    assert (
        execution_discovery_module.discover_executor_result_candidates
        is discover_executor_result_candidates
    )
    assert (
        execution_discovery_module.discover_executor_ingest_candidates
        is discover_executor_ingest_candidates
    )
    assert (
        execution_discovery_module.discover_executor_history_candidates
        is discover_executor_history_candidates
    )
    assert (
        execution_discovery_module.discover_executor_contract_candidates
        is discover_executor_contract_candidates
    )


def test_surface_discovery_module_exports_match_self_improvement_surface() -> None:
    assert (
        surface_discovery_module.discover_artifact_consistency_candidates
        is discover_artifact_consistency_candidates
    )
    assert (
        surface_discovery_module.discover_docs_drift_candidates
        is discover_docs_drift_candidates
    )
    assert (
        surface_discovery_module.discover_coverage_gap_candidates
        is discover_coverage_gap_candidates
    )


def test_self_improvement_module_keeps_extracted_discovery_defs_out_of_monolith() -> (
    None
):
    source = Path(self_improvement_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(self_improvement_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "discover_commit_isolation_candidates" not in function_names
    assert "discover_executor_history_candidates" not in function_names
    assert "discover_docs_drift_candidates" not in function_names
    assert "score_candidate" not in function_names
    assert "candidate_from_input" not in function_names
    assert "unique_candidates" not in function_names

    class_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.ClassDef)
    }
    assert "BacklogCandidate" not in class_names


def test_improvement_state_module_exports_match_self_improvement_surface() -> None:
    assert improvement_state_module.load_backlog is load_backlog
    assert improvement_state_module.open_backlog_items is open_backlog_items


def test_refactor_seams_publish_explicit_exports() -> None:
    assert {
        "BacklogCandidate",
        "candidate_from_input",
        "evidence_sources",
        "format_report_evidence",
        "merge_backlog",
        "score_candidate",
        "unique_candidates",
    } <= set(backlog_core_module.__all__)
    assert {
        "benchmark_summary_snapshot",
        "discover_benchmark_candidate_inputs",
    } <= set(benchmark_signals_module.__all__)
    assert {
        "benchmark_summaries",
        "benchmark_summary_snapshot",
    } <= set(benchmark_signal_artifacts_module.__all__)
    assert {"DiscoveryStage", "run_discovery_pipeline"} <= set(
        discovery_pipeline_module.__all__
    )
    assert {
        "BASELINE_DISCOVERY_STAGES",
        "EXECUTION_CONTRACT_DISCOVERY_STAGES",
        "EXECUTION_DISCOVERY_STAGES",
        "SURFACE_DISCOVERY_STAGES",
        "WORKTREE_DISCOVERY_STAGES",
        "LOOP_HEALTH_DISCOVERY_STAGES",
    } <= set(self_improvement_stage_groups_module.__all__)
    assert {
        "discover_executor_history_candidate_inputs",
        "load_or_synthesize_executor_dry_run_summary",
    } <= set(executor_history_signals_module.__all__)
    assert {
        "dry_run_evidence_summary",
        "dry_run_signal_set",
        "history_evidence_summary",
        "load_executor_dry_run_summary",
        "load_or_synthesize_executor_dry_run_summary",
    } <= set(executor_history_summary_module.__all__)
    assert {"executor_history_records"} <= set(executor_history_records_module.__all__)
    assert {
        "discover_executor_contract_candidates",
        "discover_executor_history_candidates",
        "discover_executor_ingest_candidates",
        "discover_executor_result_candidates",
        "discover_session_candidates",
        "discover_verification_candidates",
    } <= set(execution_discovery_module.__all__)
    assert {
        "discover_executor_ingest_candidate_inputs",
        "discover_executor_result_candidate_inputs",
    } <= set(executor_signals_module.__all__)
    assert {
        "discover_artifact_consistency_candidates",
        "discover_coverage_gap_candidates",
        "discover_docs_drift_candidates",
    } <= set(surface_discovery_module.__all__)
    assert {"discover_artifact_consistency_candidates"} <= set(
        artifact_consistency_discovery_module.__all__
    )
    assert {
        "discover_coverage_gap_candidates",
        "mixed_surface_coverage_evidence",
    } <= set(coverage_gap_discovery_module.__all__)
    assert {"discover_docs_drift_candidates"} <= set(
        docs_surface_discovery_module.__all__
    )
    assert {"git_stdout"} <= set(git_runtime_module.__all__)
    assert {
        "discover_docs_drift_candidate_inputs",
        "matching_report_evidence",
    } <= set(report_signals_module.__all__)
    assert {
        "discover_backlog_reseeding_candidate_inputs",
        "discover_empty_loop_candidate_inputs",
        "discover_repeated_fallback_family_candidate_inputs",
        "latest_self_inspection_selection_context",
    } <= set(loop_health_signals_module.__all__)
    assert {"discover_backlog_reseeding_candidate_inputs"} <= set(
        backlog_reseeding_signals_module.__all__
    )
    assert {
        "discover_empty_loop_candidate_inputs",
        "discover_repeated_fallback_family_candidate_inputs",
    } <= set(loop_history_candidates_module.__all__)
    assert {"latest_self_inspection_selection_context"} <= set(
        selection_context_module.__all__
    )
    assert {
        "discover_session_candidate_inputs",
        "discover_verification_candidate_inputs",
    } <= set(repair_signals_module.__all__)
    assert {
        "discover_artifact_hygiene_candidates",
        "discover_commit_isolation_candidates",
        "discover_deferred_cleanup_candidates",
        "discover_evidence_freshness_candidates",
        "discover_integration_gap_candidates",
        "discover_runtime_artifact_cleanup_candidates",
        "discover_worktree_risk_candidates",
    } <= set(worktree_discovery_module.__all__)
    assert {"load_backlog", "open_backlog_items"} <= set(
        improvement_state_module.__all__
    )
    assert {
        "collect_live_repository_signals",
        "render_live_repository_summary",
    } <= set(live_repository_module.__all__)
    assert {
        "compact_backlog_evidence_summary",
        "fallback_family_for_category",
        "render_loop_plan",
    } <= set(task_selection_module.__all__)
    assert {
        "compact_backlog_evidence_summary",
        "fallback_family_for_category",
        "render_live_repository_summary",
        "render_loop_plan",
        "selected_task_action_hint",
        "selected_task_validation_command",
        "worktree_action_areas",
    } <= set(self_improvement_module.__all__)
