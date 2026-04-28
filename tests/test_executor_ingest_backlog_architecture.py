"""Architecture tests for executor-ingest backlog helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_ingest as executor_ingest_module
import qa_z.executor_ingest_backlog as executor_ingest_backlog_module


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


def test_executor_ingest_module_keeps_backlog_defs_out_of_monolith() -> None:
    function_names = _executor_ingest_function_names()

    assert "backlog_implications_for_ingest" not in function_names
    assert "backlog_implication" not in function_names
    assert "unique_implications" not in function_names
    assert "stable_unique_strings" not in function_names


def test_executor_ingest_backlog_module_exposes_helpers() -> None:
    assert callable(executor_ingest_backlog_module.backlog_implications_for_ingest)
    assert callable(executor_ingest_backlog_module.backlog_implication)
    assert callable(executor_ingest_backlog_module.unique_implications)
    assert callable(executor_ingest_backlog_module.stable_unique_strings)
