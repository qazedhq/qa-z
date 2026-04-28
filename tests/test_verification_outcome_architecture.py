"""Architecture tests for internal verification outcome implementations."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.verification as verification_module


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


def test_verification_module_keeps_outcome_impl_defs_out_of_monolith() -> None:
    function_names = _verification_function_names()

    assert "_verification_summary_dict_impl" not in function_names
    assert "_verify_exit_code_impl" not in function_names
    assert "_comparison_json_impl" not in function_names


def test_verification_outcome_surface_avoids_importlib_facades() -> None:
    source = Path("src/qa_z/verification_outcome.py").read_text(encoding="utf-8")

    assert "importlib.import_module" not in source
