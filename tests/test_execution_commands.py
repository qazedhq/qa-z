"""Architecture tests for modular execution command seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.commands.execution as execution_module
import qa_z.commands.execution_repair as execution_repair_module
import qa_z.commands.execution_runs as execution_runs_module


def _execution_function_names() -> set[str]:
    source = Path(execution_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(execution_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_execution_runs_module_exports_match_execution_surface() -> None:
    assert execution_runs_module.handle_fast is execution_module.handle_fast
    assert execution_runs_module.handle_deep is execution_module.handle_deep
    assert (
        execution_runs_module.register_fast_command
        is execution_module.register_fast_command
    )
    assert (
        execution_runs_module.register_deep_command
        is execution_module.register_deep_command
    )
    assert (
        execution_runs_module.resolve_fast_selection_mode
        is execution_module.resolve_fast_selection_mode
    )
    assert (
        execution_runs_module.resolve_deep_selection_mode
        is execution_module.resolve_deep_selection_mode
    )
    assert (
        execution_runs_module.render_fast_stdout is execution_module.render_fast_stdout
    )
    assert (
        execution_runs_module.render_deep_stdout is execution_module.render_deep_stdout
    )


def test_execution_module_keeps_run_defs_out_of_monolith() -> None:
    function_names = _execution_function_names()

    assert "handle_fast" not in function_names
    assert "handle_deep" not in function_names
    assert "register_fast_command" not in function_names
    assert "register_deep_command" not in function_names
    assert "resolve_fast_selection_mode" not in function_names
    assert "resolve_deep_selection_mode" not in function_names
    assert "render_fast_stdout" not in function_names
    assert "render_deep_stdout" not in function_names


def test_execution_repair_module_exports_match_execution_surface() -> None:
    assert (
        execution_repair_module.handle_repair_prompt
        is execution_module.handle_repair_prompt
    )
    assert (
        execution_repair_module.register_repair_prompt_command
        is execution_module.register_repair_prompt_command
    )


def test_execution_module_keeps_repair_defs_out_of_monolith() -> None:
    function_names = _execution_function_names()

    assert "handle_repair_prompt" not in function_names
    assert "register_repair_prompt_command" not in function_names
