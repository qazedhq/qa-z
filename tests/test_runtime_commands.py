"""Architecture tests for modular runtime command seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.commands.runtime as runtime_module
import qa_z.commands.runtime_autonomy as runtime_autonomy_module
import qa_z.commands.runtime_benchmark as runtime_benchmark_module
import qa_z.commands.runtime_bridge as runtime_bridge_module
import qa_z.commands.runtime_executor_result as runtime_executor_result_module


def test_runtime_autonomy_module_exports_match_runtime_surface() -> None:
    assert runtime_autonomy_module.handle_autonomy is runtime_module.handle_autonomy
    assert (
        runtime_autonomy_module.register_autonomy_command
        is runtime_module.register_autonomy_command
    )


def test_runtime_module_keeps_autonomy_defs_out_of_runtime_monolith() -> None:
    source = Path(runtime_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(runtime_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "handle_autonomy" not in function_names
    assert "register_autonomy_command" not in function_names


def test_runtime_bridge_module_exports_match_runtime_surface() -> None:
    assert (
        runtime_bridge_module.handle_executor_bridge
        is runtime_module.handle_executor_bridge
    )
    assert (
        runtime_bridge_module.register_executor_bridge_command
        is runtime_module.register_executor_bridge_command
    )


def test_runtime_module_keeps_bridge_defs_out_of_runtime_monolith() -> None:
    source = Path(runtime_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(runtime_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "handle_executor_bridge" not in function_names
    assert "register_executor_bridge_command" not in function_names


def test_runtime_executor_result_module_exports_match_runtime_surface() -> None:
    assert (
        runtime_executor_result_module.handle_executor_result_ingest
        is runtime_module.handle_executor_result_ingest
    )
    assert (
        runtime_executor_result_module.handle_executor_result_dry_run
        is runtime_module.handle_executor_result_dry_run
    )
    assert (
        runtime_executor_result_module.register_executor_result_command
        is runtime_module.register_executor_result_command
    )


def test_runtime_module_keeps_executor_result_defs_out_of_runtime_monolith() -> None:
    source = Path(runtime_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(runtime_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "handle_executor_result_ingest" not in function_names
    assert "handle_executor_result_dry_run" not in function_names
    assert "register_executor_result_command" not in function_names


def test_runtime_benchmark_module_exports_match_runtime_surface() -> None:
    assert runtime_benchmark_module.handle_benchmark is runtime_module.handle_benchmark
    assert (
        runtime_benchmark_module.register_benchmark_command
        is runtime_module.register_benchmark_command
    )


def test_runtime_module_keeps_benchmark_defs_out_of_runtime_monolith() -> None:
    source = Path(runtime_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(runtime_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "handle_benchmark" not in function_names
    assert "register_benchmark_command" not in function_names
