"""Architecture tests for executor-ingest scope validation helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_ingest as executor_ingest_module
import qa_z.executor_ingest_scope as scope_module


def _executor_ingest_function_names() -> set[str]:
    source = Path(executor_ingest_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(executor_ingest_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_executor_ingest_module_keeps_scope_defs_out_of_monolith() -> None:
    function_names = _executor_ingest_function_names()

    assert "validate_result_scope" not in function_names
    assert "bridge_allowed_files" not in function_names
    assert "unexpected_changed_files" not in function_names


def test_executor_ingest_scope_module_exposes_helpers() -> None:
    assert callable(scope_module.validate_result_scope)
    assert callable(scope_module.bridge_allowed_files)
    assert callable(scope_module.unexpected_changed_files)
