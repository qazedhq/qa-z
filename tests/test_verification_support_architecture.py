"""Architecture tests for verification support helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.verification as verification_module
import qa_z.verification_support as support_module


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


def test_verification_module_keeps_support_defs_out_of_monolith() -> None:
    function_names = _verification_function_names()

    assert "fast_delta_message" not in function_names
    assert "normalize_path" not in function_names
    assert "normalize_message" not in function_names
    assert "first_nonempty" not in function_names
    assert "coerce_positive_int" not in function_names
    assert "empty_categories" not in function_names


def test_verification_support_module_exposes_helpers() -> None:
    assert callable(support_module.fast_delta_message)
    assert callable(support_module.normalize_path)
    assert callable(support_module.normalize_message)
    assert callable(support_module.first_nonempty)
    assert callable(support_module.coerce_positive_int)
    assert callable(support_module.empty_categories)
