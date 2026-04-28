"""Architecture tests for benchmark actual-summary helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.benchmark as benchmark_module
import qa_z.benchmark_executor_summaries as benchmark_executor_summaries_module
import qa_z.benchmark_run_summaries as benchmark_run_summaries_module
import qa_z.benchmark_summaries as benchmark_summaries_module


def _benchmark_function_names() -> set[str]:
    source = Path(benchmark_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(benchmark_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_benchmark_module_keeps_summary_builder_defs_out_of_monolith() -> None:
    function_names = _benchmark_function_names()

    assert "summarize_fast_actual" not in function_names
    assert "summarize_deep_actual" not in function_names
    assert "summarize_handoff_actual" not in function_names
    assert "summarize_verify_actual" not in function_names
    assert "summarize_verify_summary_actual" not in function_names
    assert "summarize_executor_bridge_actual" not in function_names
    assert "summarize_executor_result_actual" not in function_names
    assert "summarize_executor_dry_run_actual" not in function_names
    assert "summarize_artifact_actual" not in function_names


def test_benchmark_summaries_module_exposes_helpers() -> None:
    assert callable(benchmark_summaries_module.summarize_fast_actual)
    assert callable(benchmark_summaries_module.summarize_deep_actual)
    assert callable(benchmark_summaries_module.summarize_handoff_actual)
    assert callable(benchmark_summaries_module.summarize_verify_actual)
    assert callable(benchmark_summaries_module.summarize_verify_summary_actual)
    assert callable(benchmark_summaries_module.summarize_executor_bridge_actual)
    assert callable(benchmark_summaries_module.summarize_executor_result_actual)
    assert callable(benchmark_summaries_module.summarize_executor_dry_run_actual)
    assert callable(benchmark_summaries_module.summarize_artifact_actual)


def test_benchmark_summaries_module_does_not_use_importlib() -> None:
    source = Path("src/qa_z/benchmark_summaries.py").read_text(encoding="utf-8")

    assert "importlib" not in source


def test_benchmark_run_summaries_module_exports_match_surface() -> None:
    assert (
        benchmark_run_summaries_module.summarize_fast_actual
        is benchmark_module.summarize_fast_actual
    )
    assert (
        benchmark_run_summaries_module.summarize_deep_actual
        is benchmark_module.summarize_deep_actual
    )
    assert (
        benchmark_run_summaries_module.summarize_handoff_actual
        is benchmark_module.summarize_handoff_actual
    )
    assert (
        benchmark_run_summaries_module.summarize_verify_actual
        is benchmark_module.summarize_verify_actual
    )
    assert (
        benchmark_run_summaries_module.summarize_verify_summary_actual
        is benchmark_module.summarize_verify_summary_actual
    )


def test_benchmark_executor_summaries_module_exports_match_surface() -> None:
    assert (
        benchmark_executor_summaries_module.summarize_executor_bridge_actual
        is benchmark_module.summarize_executor_bridge_actual
    )
    assert (
        benchmark_executor_summaries_module.summarize_executor_result_actual
        is benchmark_module.summarize_executor_result_actual
    )
    assert (
        benchmark_executor_summaries_module.summarize_executor_dry_run_actual
        is benchmark_module.summarize_executor_dry_run_actual
    )
    assert (
        benchmark_executor_summaries_module.summarize_artifact_actual
        is benchmark_module.summarize_artifact_actual
    )
