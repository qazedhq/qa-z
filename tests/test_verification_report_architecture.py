"""Architecture tests for verification report helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.verification as verification_module
import qa_z.verification_report as verification_report_module


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


def test_verification_module_keeps_report_impl_out_of_monolith() -> None:
    function_names = _verification_function_names()

    assert "_render_verification_report_impl" not in function_names


def test_verification_report_module_exposes_helper() -> None:
    assert callable(verification_report_module.render_verification_report_impl)
