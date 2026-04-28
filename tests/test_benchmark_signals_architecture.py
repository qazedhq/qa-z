"""Architecture tests for benchmark signal seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.benchmark_signal_artifacts as benchmark_signal_artifacts_module
import qa_z.benchmark_signals as benchmark_signals_module


def _benchmark_signal_function_names() -> set[str]:
    source = Path(benchmark_signals_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(benchmark_signals_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_benchmark_signal_artifacts_module_exports_match_surface() -> None:
    assert (
        benchmark_signal_artifacts_module.benchmark_summaries
        is benchmark_signals_module.benchmark_summaries
    )
    assert (
        benchmark_signal_artifacts_module.benchmark_summary_snapshot
        is benchmark_signals_module.benchmark_summary_snapshot
    )


def test_benchmark_signals_module_keeps_artifact_defs_out_of_candidate_surface() -> (
    None
):
    function_names = _benchmark_signal_function_names()

    assert "benchmark_summaries" not in function_names
    assert "benchmark_summary_snapshot" not in function_names
