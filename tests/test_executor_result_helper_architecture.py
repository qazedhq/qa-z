"""Architecture tests for internal executor-result helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_result as executor_result_module
import qa_z.executor_result_io as executor_result_io_module
import qa_z.executor_result_parsing as executor_result_parsing_module


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


def test_executor_result_module_keeps_io_defs_out_of_monolith() -> None:
    function_names = _executor_result_function_names()

    assert "write_json" not in function_names
    assert "read_json_object" not in function_names


def test_executor_result_module_keeps_parsing_defs_out_of_monolith() -> None:
    function_names = _executor_result_function_names()

    assert "required_string" not in function_names
    assert "optional_string" not in function_names
    assert "optional_int" not in function_names
    assert "string_list" not in function_names
    assert "list_of_string_lists" not in function_names


def test_executor_result_io_module_exposes_helpers() -> None:
    assert callable(executor_result_io_module.write_json)
    assert callable(executor_result_io_module.read_json_object)


def test_executor_result_parsing_module_exposes_helpers() -> None:
    assert callable(executor_result_parsing_module.required_string)
    assert callable(executor_result_parsing_module.optional_int)
    assert callable(executor_result_parsing_module.list_of_string_lists)
