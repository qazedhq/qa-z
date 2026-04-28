"""Architecture tests for executor-result runtime stdout seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.commands.runtime as runtime_module
import qa_z.commands.runtime_executor_result as runtime_executor_result_module
import qa_z.commands.runtime_executor_result_stdout as runtime_executor_result_stdout_module


def _runtime_executor_result_function_names() -> set[str]:
    source = Path(runtime_executor_result_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(runtime_executor_result_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_runtime_executor_result_stdout_module_exports_match_runtime_surface() -> None:
    assert (
        runtime_executor_result_stdout_module.render_executor_result_dry_run_stdout
        is runtime_module.render_executor_result_dry_run_stdout
    )
    assert (
        runtime_executor_result_stdout_module.dry_run_text_field
        is runtime_module.dry_run_text_field
    )
    assert (
        runtime_executor_result_stdout_module.dry_run_rule_counts
        is runtime_module.dry_run_rule_counts
    )
    assert (
        runtime_executor_result_stdout_module.dry_run_action_summaries
        is runtime_module.dry_run_action_summaries
    )


def test_runtime_executor_result_module_keeps_stdout_defs_out_of_command_module() -> (
    None
):
    function_names = _runtime_executor_result_function_names()

    assert "render_executor_result_dry_run_stdout" not in function_names
    assert "dry_run_text_field" not in function_names
    assert "dry_run_rule_counts" not in function_names
    assert "dry_run_action_summaries" not in function_names
