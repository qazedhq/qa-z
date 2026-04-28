"""Architecture tests for benchmark fixture execution helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.benchmark as benchmark_module
import qa_z.benchmark_executor_execution as benchmark_executor_execution_module
import qa_z.benchmark_executor_loop_context as benchmark_executor_loop_context_module
import qa_z.benchmark_execution as benchmark_execution_module


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


def test_benchmark_module_keeps_execution_defs_out_of_monolith() -> None:
    function_names = _benchmark_function_names()

    assert "execute_fast_fixture" not in function_names
    assert "execute_deep_fixture" not in function_names
    assert "execute_handoff_fixture" not in function_names
    assert "execute_verify_fixture" not in function_names
    assert "execute_executor_result_fixture" not in function_names
    assert "execute_executor_bridge_fixture" not in function_names
    assert "write_benchmark_loop_context" not in function_names
    assert "execute_executor_dry_run_fixture" not in function_names


def test_benchmark_execution_module_exposes_helpers() -> None:
    assert callable(benchmark_execution_module.execute_fast_fixture)
    assert callable(benchmark_execution_module.execute_deep_fixture)
    assert callable(benchmark_execution_module.execute_handoff_fixture)
    assert callable(benchmark_execution_module.execute_verify_fixture)


def test_benchmark_executor_execution_module_exposes_helpers() -> None:
    assert callable(benchmark_executor_execution_module.execute_executor_result_fixture)
    assert callable(benchmark_executor_execution_module.execute_executor_bridge_fixture)
    assert callable(
        benchmark_executor_execution_module.execute_executor_dry_run_fixture
    )
    assert callable(benchmark_executor_loop_context_module.write_benchmark_loop_context)


def test_benchmark_execution_split_modules_do_not_use_importlib() -> None:
    for relative_path in (
        "src/qa_z/benchmark_execution.py",
        "src/qa_z/benchmark_executor_execution.py",
    ):
        source = Path(relative_path).read_text(encoding="utf-8")
        assert "importlib" not in source


def test_benchmark_execution_split_modules_match_surface() -> None:
    assert (
        benchmark_execution_module.execute_fast_fixture
        is benchmark_module.execute_fast_fixture
    )
    assert (
        benchmark_execution_module.execute_deep_fixture
        is benchmark_module.execute_deep_fixture
    )
    assert (
        benchmark_execution_module.execute_handoff_fixture
        is benchmark_module.execute_handoff_fixture
    )
    assert (
        benchmark_execution_module.execute_verify_fixture
        is benchmark_module.execute_verify_fixture
    )
    assert (
        benchmark_executor_execution_module.execute_executor_result_fixture
        is benchmark_module.execute_executor_result_fixture
    )
    assert (
        benchmark_executor_execution_module.execute_executor_bridge_fixture
        is benchmark_module.execute_executor_bridge_fixture
    )
    assert (
        benchmark_executor_loop_context_module.write_benchmark_loop_context
        is benchmark_module.write_benchmark_loop_context
    )
    assert (
        benchmark_executor_execution_module.execute_executor_dry_run_fixture
        is benchmark_module.execute_executor_dry_run_fixture
    )
