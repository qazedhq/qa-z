"""Architecture tests for executor-oriented execution discovery seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.execution_discovery as execution_discovery_module
import qa_z.execution_executor_candidates as execution_executor_candidates_module


def _execution_discovery_function_names() -> set[str]:
    source = Path(execution_discovery_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(execution_discovery_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_execution_executor_candidates_module_exports_match_discovery_surface() -> None:
    assert (
        execution_executor_candidates_module.discover_executor_result_candidates
        is execution_discovery_module.discover_executor_result_candidates
    )
    assert (
        execution_executor_candidates_module.discover_executor_ingest_candidates
        is execution_discovery_module.discover_executor_ingest_candidates
    )


def test_execution_discovery_module_keeps_executor_result_ingest_defs_out_of_mixed_module() -> (
    None
):
    function_names = _execution_discovery_function_names()

    assert "discover_executor_result_candidates" not in function_names
    assert "discover_executor_ingest_candidates" not in function_names
