"""Architecture tests for internal executor-ingest helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_ingest as executor_ingest_module
import qa_z.executor_ingest_checks as executor_ingest_checks_module


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


def test_executor_ingest_module_keeps_check_defs_out_of_monolith() -> None:
    function_names = _executor_ingest_function_names()

    assert "empty_check" not in function_names
    assert "failed_check" not in function_names
    assert "build_freshness_check" not in function_names
    assert "build_provenance_check" not in function_names
    assert "status_warnings_for_result" not in function_names
    assert "validation_warnings_for_result" not in function_names
    assert "verify_resume_status_for_result" not in function_names
    assert "accepted_ingest_status" not in function_names
    assert "next_recommendation_for_ingest" not in function_names


def test_executor_ingest_checks_module_exposes_helpers() -> None:
    assert callable(executor_ingest_checks_module.empty_check)
    assert callable(executor_ingest_checks_module.failed_check)
    assert callable(executor_ingest_checks_module.build_freshness_check)
    assert callable(executor_ingest_checks_module.build_provenance_check)
    assert callable(executor_ingest_checks_module.status_warnings_for_result)
    assert callable(executor_ingest_checks_module.validation_warnings_for_result)
    assert callable(executor_ingest_checks_module.verify_resume_status_for_result)
    assert callable(executor_ingest_checks_module.accepted_ingest_status)
    assert callable(executor_ingest_checks_module.next_recommendation_for_ingest)
