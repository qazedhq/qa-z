"""Architecture tests for executor-ingest support helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_ingest as executor_ingest_module
import qa_z.executor_ingest_support as support_module


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


def test_executor_ingest_module_keeps_support_defs_out_of_monolith() -> None:
    function_names = _executor_ingest_function_names()

    assert "current_utc_timestamp" not in function_names
    assert "resolve_relative_path" not in function_names
    assert "format_relative_path" not in function_names
    assert "normalize_repo_path" not in function_names
    assert "read_json_object" not in function_names
    assert "optional_text" not in function_names
    assert "parse_timestamp" not in function_names


def test_executor_ingest_support_module_exposes_helpers() -> None:
    assert callable(support_module.current_utc_timestamp)
    assert callable(support_module.resolve_relative_path)
    assert callable(support_module.format_relative_path)
    assert callable(support_module.normalize_repo_path)
    assert callable(support_module.read_json_object)
    assert callable(support_module.optional_text)
    assert callable(support_module.parse_timestamp)
