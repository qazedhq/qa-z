"""Architecture tests for internal executor-ingest render helpers."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_ingest as executor_ingest_module
import qa_z.executor_ingest_render_support as render_support_module


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


def test_executor_ingest_module_keeps_render_support_defs_out_of_monolith() -> None:
    function_names = _executor_ingest_function_names()

    assert "ingest_text_field" not in function_names
    assert "ingest_check_stdout_line" not in function_names
    assert "ingest_warning_stdout_summary" not in function_names
    assert "ingest_implication_stdout_summary" not in function_names


def test_executor_ingest_render_support_module_exposes_helpers() -> None:
    assert callable(render_support_module.ingest_text_field)
    assert callable(render_support_module.ingest_check_stdout_line)
    assert callable(render_support_module.ingest_warning_stdout_summary)
    assert callable(render_support_module.ingest_implication_stdout_summary)
