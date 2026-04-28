"""Architecture tests for repair-session guide helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.repair_session as repair_session_module
import qa_z.repair_session_guides as guides_module


def _repair_session_function_names() -> set[str]:
    source = Path(repair_session_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(repair_session_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_repair_session_module_keeps_guide_defs_out_of_monolith() -> None:
    function_names = _repair_session_function_names()

    assert "write_executor_guide" not in function_names
    assert "render_executor_guide" not in function_names


def test_repair_session_guides_module_exposes_helpers() -> None:
    assert callable(guides_module.write_executor_guide)
    assert callable(guides_module.render_executor_guide)
