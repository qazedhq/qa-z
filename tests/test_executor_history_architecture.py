"""Architecture tests for executor-history seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_history as executor_history_module
import qa_z.executor_history_paths as executor_history_paths_module
import qa_z.executor_history_signals as executor_history_signals_module
import qa_z.executor_history_store as executor_history_store_module
import qa_z.executor_history_summary as executor_history_summary_module
import qa_z.executor_history_support as executor_history_support_module


def _executor_history_function_names() -> set[str]:
    source = Path(executor_history_signals_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(executor_history_signals_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def _executor_history_surface_function_names() -> set[str]:
    source = Path(executor_history_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(executor_history_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_executor_history_summary_module_exports_match_signal_surface() -> None:
    assert (
        executor_history_summary_module.load_or_synthesize_executor_dry_run_summary
        is executor_history_signals_module.load_or_synthesize_executor_dry_run_summary
    )
    assert (
        executor_history_summary_module.history_evidence_summary
        is executor_history_signals_module.history_evidence_summary
    )
    assert (
        executor_history_summary_module.dry_run_evidence_summary
        is executor_history_signals_module.dry_run_evidence_summary
    )


def test_executor_history_signals_module_keeps_summary_defs_out_of_candidate_surface() -> (
    None
):
    function_names = _executor_history_function_names()

    assert "load_executor_dry_run_summary" not in function_names
    assert "load_or_synthesize_executor_dry_run_summary" not in function_names
    assert "history_evidence_summary" not in function_names
    assert "dry_run_evidence_summary" not in function_names
    assert "dry_run_signal_set" not in function_names


def test_executor_history_support_module_exports_match_surface() -> None:
    assert (
        executor_history_support_module.write_json is executor_history_module.write_json
    )
    assert (
        executor_history_support_module.allocate_attempt_id
        is executor_history_module.allocate_attempt_id
    )
    assert (
        executor_history_support_module.legacy_attempt_base
        is executor_history_module.legacy_attempt_base
    )
    assert executor_history_support_module.slugify is executor_history_module.slugify
    assert (
        executor_history_support_module.resolve_path
        is executor_history_module.resolve_path
    )


def test_executor_history_paths_module_exports_match_surface() -> None:
    assert (
        executor_history_paths_module.executor_results_dir
        is executor_history_module.executor_results_dir
    )
    assert (
        executor_history_paths_module.executor_result_attempts_dir
        is executor_history_module.executor_result_attempts_dir
    )
    assert (
        executor_history_paths_module.executor_result_history_path
        is executor_history_module.executor_result_history_path
    )
    assert (
        executor_history_paths_module.executor_result_dry_run_summary_path
        is executor_history_module.executor_result_dry_run_summary_path
    )
    assert (
        executor_history_paths_module.executor_result_dry_run_report_path
        is executor_history_module.executor_result_dry_run_report_path
    )


def test_executor_history_store_module_exports_match_surface() -> None:
    assert (
        executor_history_store_module.load_executor_result_history
        is executor_history_module.load_executor_result_history
    )
    assert (
        executor_history_store_module.append_executor_result_attempt
        is executor_history_module.append_executor_result_attempt
    )
    assert (
        executor_history_store_module.ensure_session_executor_history
        is executor_history_module.ensure_session_executor_history
    )


def test_executor_history_module_keeps_store_defs_out_of_monolith() -> None:
    function_names = _executor_history_surface_function_names()

    assert "load_executor_result_history" not in function_names
    assert "append_executor_result_attempt" not in function_names
    assert "ensure_session_executor_history" not in function_names
    assert "write_json" not in function_names
    assert "allocate_attempt_id" not in function_names
    assert "legacy_attempt_base" not in function_names
    assert "slugify" not in function_names
    assert "resolve_path" not in function_names
    assert "executor_results_dir" not in function_names
    assert "executor_result_attempts_dir" not in function_names
    assert "executor_result_history_path" not in function_names
    assert "executor_result_dry_run_summary_path" not in function_names
    assert "executor_result_dry_run_report_path" not in function_names


def test_executor_history_module_uses_explicit_imports() -> None:
    source = Path(executor_history_module.__file__).read_text(encoding="utf-8")

    assert "import importlib" not in source
    assert "importlib.import_module" not in source
