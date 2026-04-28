"""Architecture tests for modular session command seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.commands.session_repair as session_repair_module
import qa_z.commands.session_verify as session_verify_module
import qa_z.commands.sessioning as sessioning_module


def _sessioning_function_names() -> set[str]:
    source = Path(sessioning_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(sessioning_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_session_verify_module_exports_match_sessioning_surface() -> None:
    assert session_verify_module.handle_verify is sessioning_module.handle_verify
    assert (
        session_verify_module.register_verify_command
        is sessioning_module.register_verify_command
    )
    assert (
        session_verify_module.render_verify_stdout
        is sessioning_module.render_verify_stdout
    )


def test_sessioning_module_keeps_verify_defs_out_of_monolith() -> None:
    function_names = _sessioning_function_names()

    assert "handle_verify" not in function_names
    assert "register_verify_command" not in function_names
    assert "render_verify_stdout" not in function_names


def test_session_repair_module_exports_match_sessioning_surface() -> None:
    assert (
        session_repair_module.handle_repair_session_start
        is sessioning_module.handle_repair_session_start
    )
    assert (
        session_repair_module.handle_repair_session_status
        is sessioning_module.handle_repair_session_status
    )
    assert (
        session_repair_module.handle_repair_session_verify
        is sessioning_module.handle_repair_session_verify
    )
    assert (
        session_repair_module.register_repair_session_command
        is sessioning_module.register_repair_session_command
    )


def test_sessioning_module_keeps_repair_defs_out_of_monolith() -> None:
    function_names = _sessioning_function_names()

    assert "handle_repair_session_start" not in function_names
    assert "handle_repair_session_status" not in function_names
    assert "handle_repair_session_verify" not in function_names
    assert "register_repair_session_command" not in function_names
