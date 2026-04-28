"""Architecture tests for executor-ingest verification helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body


def test_executor_ingest_verification_module_exists() -> None:
    assert Path("src/qa_z/executor_ingest_verification.py").exists()


def test_executor_ingest_monolith_no_longer_defines_verify_impl() -> None:
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

    assert "_verify_repair_session_impl" not in function_names


def test_executor_ingest_runtime_wrapper_targets_verification_module() -> None:
    source = Path("src/qa_z/executor_ingest_runtime.py").read_text(encoding="utf-8")

    assert "executor_ingest_verification" in source
    assert "_verify_repair_session_impl" not in source
