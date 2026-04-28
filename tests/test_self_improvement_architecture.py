"""Architecture tests for extracted self-improvement seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.self_improvement_constants as self_improvement_constants_module


TESTS_DIR = Path(__file__).resolve().parent
GIANT_TEST_PATH = TESTS_DIR / "test_self_improvement.py"
TEST_SUPPORT_PATH = TESTS_DIR / "self_improvement_test_support.py"
RESEED_POLICY_TEST_PATH = TESTS_DIR / "test_self_improvement_reseed_policy.py"
SIGNAL_INPUT_TEST_PATH = TESTS_DIR / "test_self_improvement_signal_inputs.py"


def test_self_improvement_constants_module_exports_expected_values() -> None:
    assert self_improvement_constants_module.SELF_IMPROVEMENT_SCHEMA_VERSION == 1
    assert self_improvement_constants_module.EXPECTED_COMMAND_DOC_TERMS == (
        "self-inspect",
        "select-next",
        "backlog",
    )
    assert self_improvement_constants_module.DIRTY_WORKTREE_MODIFIED_THRESHOLD == 10
    assert self_improvement_constants_module.DIRTY_WORKTREE_TOTAL_THRESHOLD == 30
    assert set(self_improvement_constants_module.REPORT_EVIDENCE_FILES) == {
        "current_state",
        "roadmap",
        "worktree_triage",
        "worktree_commit_plan",
    }


def test_extracted_discovery_modules_do_not_depend_on_self_improvement_monolith() -> (
    None
):
    for path in (
        Path("src/qa_z/execution_discovery.py"),
        Path("src/qa_z/surface_discovery.py"),
        Path("src/qa_z/worktree_discovery.py"),
    ):
        source = path.read_text(encoding="utf-8")
        tree = compile(str(source), str(path), "exec", flags=ast.PyCF_ONLY_AST)
        function_names = {
            node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
        }
        imported_modules = {
            alias.name
            for node in module_body(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }

        assert "_si" not in function_names
        assert "qa_z.self_improvement" not in imported_modules


def test_self_improvement_giant_test_file_stays_below_layout_budget() -> None:
    line_count = len(GIANT_TEST_PATH.read_text(encoding="utf-8").splitlines())

    assert line_count <= 1300


def test_self_improvement_giant_test_file_does_not_reclaim_extracted_seams() -> None:
    source = GIANT_TEST_PATH.read_text(encoding="utf-8")
    tree = compile(
        source,
        str(GIANT_TEST_PATH),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "write_incomplete_session" not in function_names
    assert "write_fixture_index" not in function_names
    assert (
        "test_score_candidate_uses_formula_and_grounded_bonuses" not in function_names
    )
    assert (
        "test_classify_worktree_path_area_uses_stable_repository_buckets"
        not in function_names
    )
    assert (
        "test_self_inspection_skips_stale_dated_deferred_cleanup_report"
        not in function_names
    )
    assert (
        "test_self_inspection_skips_stale_dated_integration_report"
        not in function_names
    )
    assert (
        "test_self_inspection_skips_stale_dated_commit_isolation_report"
        not in function_names
    )
    assert (
        "test_self_inspection_writes_report_and_updates_backlog" not in function_names
    )
    assert (
        "test_self_inspection_keeps_in_progress_backlog_items_when_not_reobserved"
        not in function_names
    )


def test_self_improvement_test_support_centralizes_live_repository_patch_boundary() -> (
    None
):
    support_source = TEST_SUPPORT_PATH.read_text(encoding="utf-8")

    assert (
        support_source.count("qa_z.self_improvement.collect_live_repository_signals")
        == 1
    )

    for path in (
        GIANT_TEST_PATH,
        TESTS_DIR / "test_self_improvement_lifecycle.py",
        RESEED_POLICY_TEST_PATH,
    ):
        assert (
            "qa_z.self_improvement.collect_live_repository_signals"
            not in path.read_text(encoding="utf-8")
        )


def test_reseed_policy_file_does_not_reclaim_coverage_policy_tests() -> None:
    source = RESEED_POLICY_TEST_PATH.read_text(encoding="utf-8")
    tree = compile(
        source,
        str(RESEED_POLICY_TEST_PATH),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert (
        "test_score_candidate_boosts_reseed_and_service_readiness_signals"
        not in function_names
    )
    assert (
        "test_self_inspection_keeps_coverage_gap_when_mixed_fixture_only_covers_fast_and_handoff"
        not in function_names
    )
    assert (
        "test_self_inspection_skips_coverage_gap_when_fast_deep_and_handoff_mixed_fixtures_exist"
        not in function_names
    )


def test_signal_input_giant_file_does_not_reclaim_benchmark_or_report_signal_tests() -> (
    None
):
    source = SIGNAL_INPUT_TEST_PATH.read_text(encoding="utf-8")
    tree = compile(
        source,
        str(SIGNAL_INPUT_TEST_PATH),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert (
        "test_discover_benchmark_candidate_inputs_synthesizes_summary_level_failure"
        not in function_names
    )
    assert (
        "test_discover_docs_drift_candidate_inputs_records_report_freshness_proof"
        not in function_names
    )
    assert (
        "test_discover_docs_drift_candidate_inputs_skips_future_dated_report_evidence"
        not in function_names
    )
    assert (
        "test_discover_executor_result_candidate_inputs_uses_manifest_fallback"
        not in function_names
    )
    assert (
        "test_discover_executor_ingest_candidate_inputs_skips_partial_implications"
        not in function_names
    )
    assert (
        "test_load_or_synthesize_executor_dry_run_summary_marks_history_fallback"
        not in function_names
    )
    assert (
        "test_discover_executor_history_candidate_inputs_records_fallback_evidence_source"
        not in function_names
    )
    assert (
        "test_discover_empty_loop_candidate_inputs_uses_recent_history_chain"
        not in function_names
    )
    assert (
        "test_latest_self_inspection_selection_context_reads_loop_local_provenance"
        not in function_names
    )
    assert "test_git_stdout_runs_git_with_utf8_and_returns_text" not in function_names
    assert "test_git_stdout_returns_none_for_git_failures" not in function_names
    assert (
        "test_git_stdout_returns_none_when_git_invocation_raises_oserror"
        not in function_names
    )
    assert (
        "test_discover_verification_candidate_inputs_normalizes_verdict_text"
        not in function_names
    )
    assert (
        "test_discover_session_candidate_inputs_normalizes_incomplete_state_text"
        not in function_names
    )


def test_signal_input_pipeline_contract_file_stays_compact() -> None:
    line_count = len(SIGNAL_INPUT_TEST_PATH.read_text(encoding="utf-8").splitlines())

    assert line_count <= 80
