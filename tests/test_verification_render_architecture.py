"""Architecture tests for verification render helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.verification as verification_module
import qa_z.verification_render as verification_render_module


def _verification_function_names() -> set[str]:
    source = Path(verification_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(verification_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_verification_module_keeps_render_defs_out_of_monolith() -> None:
    function_names = _verification_function_names()

    assert "render_fast_category" not in function_names
    assert "render_finding_category" not in function_names


def test_verification_render_module_exposes_helpers() -> None:
    assert callable(verification_render_module.render_fast_category)
    assert callable(verification_render_module.render_finding_category)
