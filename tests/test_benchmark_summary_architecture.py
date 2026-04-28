"""Architecture tests for benchmark summary helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.benchmark as benchmark_module
import qa_z.benchmark_summary as benchmark_summary_module


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


def test_benchmark_module_keeps_summary_defs_out_of_monolith() -> None:
    function_names = _benchmark_function_names()

    assert "categorize_result" not in function_names
    assert "category_status" not in function_names
    assert "build_benchmark_summary" not in function_names
    assert "benchmark_snapshot" not in function_names


def test_benchmark_summary_module_exposes_helpers() -> None:
    assert callable(benchmark_summary_module.categorize_result)
    assert callable(benchmark_summary_module.category_status)
    assert callable(benchmark_summary_module.build_benchmark_summary)
    assert callable(benchmark_summary_module.benchmark_snapshot)
