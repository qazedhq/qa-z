"""Architecture tests for benchmark expectation comparison helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.benchmark as benchmark_module
import qa_z.benchmark_compare as benchmark_compare_module
import qa_z.benchmark_compare_support as benchmark_compare_support_module
import qa_z.benchmark_expectation_keys as benchmark_expectation_keys_module


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


def test_benchmark_module_keeps_compare_defs_out_of_monolith() -> None:
    function_names = _benchmark_function_names()

    assert "compare_expected" not in function_names
    assert "compare_section" not in function_names
    assert "compare_absent_list" not in function_names
    assert "compare_expected_list" not in function_names
    assert "compare_minimum" not in function_names
    assert "compare_maximum" not in function_names
    assert "expectation_actual_key" not in function_names
    assert "has_policy_expectation" not in function_names


def test_benchmark_compare_module_exposes_helpers() -> None:
    assert callable(benchmark_compare_module.compare_expected)
    assert callable(benchmark_compare_module.compare_section)
    assert callable(benchmark_compare_module.compare_absent_list)
    assert callable(benchmark_compare_module.compare_expected_list)
    assert callable(benchmark_compare_module.compare_minimum)
    assert callable(benchmark_compare_module.compare_maximum)
    assert callable(benchmark_compare_module.expectation_actual_key)
    assert callable(benchmark_compare_module.has_policy_expectation)


def test_benchmark_compare_support_modules_match_public_surface() -> None:
    assert (
        benchmark_compare_support_module.compare_absent_list
        is benchmark_compare_module.compare_absent_list
    )
    assert (
        benchmark_compare_support_module.compare_expected_list
        is benchmark_compare_module.compare_expected_list
    )
    assert (
        benchmark_compare_support_module.compare_minimum
        is benchmark_compare_module.compare_minimum
    )
    assert (
        benchmark_compare_support_module.compare_maximum
        is benchmark_compare_module.compare_maximum
    )
    assert (
        benchmark_expectation_keys_module.expectation_actual_key
        is benchmark_compare_module.expectation_actual_key
    )
    assert (
        benchmark_expectation_keys_module.has_policy_expectation
        is benchmark_compare_module.has_policy_expectation
    )
