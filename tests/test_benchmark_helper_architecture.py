"""Architecture tests for internal benchmark helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.benchmark as benchmark_module
import qa_z.benchmark_helpers as benchmark_helpers_module
import qa_z.benchmark_metrics as benchmark_metrics_module


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


def test_benchmark_module_keeps_helper_defs_out_of_monolith() -> None:
    function_names = _benchmark_function_names()

    assert "format_path" not in function_names
    assert "read_json_object" not in function_names
    assert "coerce_mapping" not in function_names
    assert "string_list" not in function_names
    assert "coerce_number" not in function_names
    assert "aggregate_filter_reasons" not in function_names
    assert "unique_strings" not in function_names


def test_benchmark_module_keeps_metric_defs_out_of_monolith() -> None:
    function_names = _benchmark_function_names()

    assert "category_rate" not in function_names
    assert "rate" not in function_names
    assert "category_coverage_label" not in function_names


def test_benchmark_helpers_module_exposes_helpers() -> None:
    assert callable(benchmark_helpers_module.format_path)
    assert callable(benchmark_helpers_module.read_json_object)
    assert callable(benchmark_helpers_module.aggregate_filter_reasons)


def test_benchmark_metrics_module_exposes_helpers() -> None:
    assert callable(benchmark_metrics_module.category_rate)
    assert callable(benchmark_metrics_module.rate)
    assert callable(benchmark_metrics_module.category_coverage_label)
