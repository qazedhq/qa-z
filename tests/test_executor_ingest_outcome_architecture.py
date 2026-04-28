"""Architecture tests for executor-ingest outcome helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_ingest as executor_ingest_module
import qa_z.executor_ingest_outcome as outcome_module


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


def test_executor_ingest_module_keeps_outcome_defs_out_of_monolith() -> None:
    function_names = _executor_ingest_function_names()

    assert "record_attempt_if_possible" not in function_names
    assert "ingest_source_context" not in function_names
    assert "finalized_ingest_outcome" not in function_names
    assert "rejected_ingest_outcome" not in function_names
    assert "executor_result_id" not in function_names
    assert "compact_timestamp" not in function_names


def test_executor_ingest_outcome_module_exposes_helpers() -> None:
    assert callable(outcome_module.record_attempt_if_possible)
    assert callable(outcome_module.ingest_source_context)
    assert callable(outcome_module.finalized_ingest_outcome)
    assert callable(outcome_module.rejected_ingest_outcome)
    assert callable(outcome_module.executor_result_id)
    assert callable(outcome_module.compact_timestamp)
