"""Architecture tests for executor-history record seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_history_records as executor_history_records_module
import qa_z.executor_history_signals as executor_history_signals_module


def _executor_history_signal_function_names() -> set[str]:
    source = Path(executor_history_signals_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(executor_history_signals_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_executor_history_records_module_exports_match_signal_surface() -> None:
    assert callable(executor_history_records_module.executor_history_records)


def test_executor_history_signals_module_keeps_record_loading_out_of_policy_surface() -> (
    None
):
    function_names = _executor_history_signal_function_names()

    assert "executor_history_records" not in function_names
