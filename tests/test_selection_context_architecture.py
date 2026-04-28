"""Architecture tests for selection-context seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.loop_health_signals as loop_health_signals_module
import qa_z.selection_context as selection_context_module


def _loop_health_function_names() -> set[str]:
    source = Path(loop_health_signals_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(loop_health_signals_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_selection_context_module_exports_match_loop_health_surface() -> None:
    assert (
        selection_context_module.latest_self_inspection_selection_context
        is loop_health_signals_module.latest_self_inspection_selection_context
    )


def test_loop_health_module_keeps_selection_context_defs_out_of_candidate_module() -> (
    None
):
    function_names = _loop_health_function_names()

    assert "latest_self_inspection_selection_context" not in function_names
    assert "read_json_object" not in function_names
