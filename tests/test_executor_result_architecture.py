"""Architecture tests for executor-result seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_result as executor_result_module
import qa_z.executor_result_artifacts as executor_result_artifacts_module
import qa_z.executor_result_summary as executor_result_summary_module


def _executor_result_function_names() -> set[str]:
    source = Path(executor_result_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(executor_result_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_executor_result_artifacts_module_exports_match_surface() -> None:
    assert (
        executor_result_artifacts_module.executor_result_template
        is executor_result_module.executor_result_template
    )
    assert (
        executor_result_artifacts_module.load_executor_result
        is executor_result_module.load_executor_result
    )
    assert (
        executor_result_artifacts_module.resolve_bridge_manifest_path
        is executor_result_module.resolve_bridge_manifest_path
    )
    assert (
        executor_result_artifacts_module.load_bridge_manifest
        is executor_result_module.load_bridge_manifest
    )
    assert (
        executor_result_artifacts_module.store_executor_result
        is executor_result_module.store_executor_result
    )


def test_executor_result_summary_module_exports_match_surface() -> None:
    assert (
        executor_result_summary_module.ingest_summary_dict
        is executor_result_module.ingest_summary_dict
    )
    assert (
        executor_result_summary_module.next_recommendation_for_result
        is executor_result_module.next_recommendation_for_result
    )


def test_executor_result_module_keeps_public_defs_out_of_monolith() -> None:
    function_names = _executor_result_function_names()

    assert "executor_result_template" not in function_names
    assert "load_executor_result" not in function_names
    assert "resolve_bridge_manifest_path" not in function_names
    assert "load_bridge_manifest" not in function_names
    assert "store_executor_result" not in function_names
    assert "ingest_summary_dict" not in function_names
    assert "next_recommendation_for_result" not in function_names


def test_executor_result_module_uses_explicit_imports() -> None:
    source = Path(executor_result_module.__file__).read_text(encoding="utf-8")

    assert "import importlib" not in source
    assert "importlib.import_module" not in source
