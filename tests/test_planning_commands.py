"""Architecture tests for modular planning command seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.commands.planning as planning_module
import qa_z.commands.planning_backlog as planning_backlog_module
import qa_z.commands.planning_inspect as planning_inspect_module
import qa_z.commands.planning_select as planning_select_module


def _planning_function_names() -> set[str]:
    source = Path(planning_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(planning_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_planning_inspect_module_exports_match_planning_surface() -> None:
    assert (
        planning_inspect_module.handle_self_inspect
        is planning_module.handle_self_inspect
    )
    assert (
        planning_inspect_module.register_self_inspect_command
        is planning_module.register_self_inspect_command
    )


def test_planning_module_keeps_inspect_defs_out_of_monolith() -> None:
    function_names = _planning_function_names()

    assert "handle_self_inspect" not in function_names
    assert "register_self_inspect_command" not in function_names


def test_planning_select_module_exports_match_planning_surface() -> None:
    assert (
        planning_select_module.handle_select_next is planning_module.handle_select_next
    )
    assert (
        planning_select_module.register_select_next_command
        is planning_module.register_select_next_command
    )


def test_planning_module_keeps_select_defs_out_of_monolith() -> None:
    function_names = _planning_function_names()

    assert "handle_select_next" not in function_names
    assert "register_select_next_command" not in function_names


def test_planning_backlog_module_exports_match_planning_surface() -> None:
    assert planning_backlog_module.handle_backlog is planning_module.handle_backlog
    assert (
        planning_backlog_module.register_backlog_command
        is planning_module.register_backlog_command
    )


def test_planning_module_keeps_backlog_defs_out_of_monolith() -> None:
    function_names = _planning_function_names()

    assert "handle_backlog" not in function_names
    assert "register_backlog_command" not in function_names
