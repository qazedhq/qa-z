"""Architecture tests for executor-result fa챌ade boundaries."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body


def test_executor_result_monolith_no_longer_defines_impl_helpers() -> None:
    source = Path("src/qa_z/executor_result.py").read_text(encoding="utf-8")
    tree = compile(
        source,
        "src/qa_z/executor_result.py",
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "_executor_result_template_impl" not in function_names
    assert "_load_executor_result_impl" not in function_names
    assert "_resolve_bridge_manifest_path_impl" not in function_names
    assert "_load_bridge_manifest_impl" not in function_names
    assert "_store_executor_result_impl" not in function_names
    assert "_ingest_summary_dict_impl" not in function_names
    assert "_next_recommendation_for_result_impl" not in function_names


def test_executor_result_monolith_routes_impl_helpers_through_split_modules() -> None:
    source = Path("src/qa_z/executor_result.py").read_text(encoding="utf-8")

    assert "executor_result_artifacts" in source
    assert "executor_result_summary" in source
