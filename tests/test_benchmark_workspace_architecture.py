"""Architecture tests for benchmark workspace and lock helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.benchmark as benchmark_module
import qa_z.benchmark_workspace as benchmark_workspace_module


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


def test_benchmark_module_keeps_workspace_defs_out_of_monolith() -> None:
    function_names = _benchmark_function_names()

    assert "benchmark_results_lock" not in function_names
    assert "_utc_timestamp" not in function_names
    assert "_read_benchmark_lock_details" not in function_names
    assert "prepare_workspace" not in function_names
    assert "install_support_files" not in function_names
    assert "fixture_path_environment" not in function_names
    assert "reset_directory" not in function_names
    assert "rmtree_with_retries" not in function_names
    assert "unlink_with_retries" not in function_names


def test_benchmark_workspace_module_exposes_helpers() -> None:
    assert callable(benchmark_workspace_module.benchmark_results_lock)
    assert callable(benchmark_workspace_module.prepare_workspace)
    assert callable(benchmark_workspace_module.install_support_files)
    assert callable(benchmark_workspace_module.fixture_path_environment)
    assert callable(benchmark_workspace_module.reset_directory)
    assert callable(benchmark_workspace_module.rmtree_with_retries)
    assert callable(benchmark_workspace_module.unlink_with_retries)
