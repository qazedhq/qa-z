"""Architecture tests for executor-ingest flow helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body


def test_executor_ingest_flow_module_exists() -> None:
    assert Path("src/qa_z/executor_ingest_flow.py").exists()


def test_executor_ingest_monolith_no_longer_defines_ingest_impl() -> None:
    source = Path("src/qa_z/executor_ingest.py").read_text(encoding="utf-8")
    tree = compile(
        source,
        "src/qa_z/executor_ingest.py",
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "_ingest_executor_result_artifact_impl" not in function_names


def test_executor_ingest_runtime_wrapper_targets_flow_module() -> None:
    source = Path("src/qa_z/executor_ingest_runtime.py").read_text(encoding="utf-8")

    assert "executor_ingest_flow" in source
    assert "_ingest_executor_result_artifact_impl" not in source
