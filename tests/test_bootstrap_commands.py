"""Architecture tests for modular bootstrap command seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.commands.bootstrap as bootstrap_module
import qa_z.commands.bootstrap_init as bootstrap_init_module
import qa_z.commands.bootstrap_plan as bootstrap_plan_module


def _bootstrap_function_names() -> set[str]:
    source = Path(bootstrap_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(bootstrap_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_bootstrap_init_module_exports_match_bootstrap_surface() -> None:
    assert bootstrap_init_module.handle_init is bootstrap_module.handle_init
    assert (
        bootstrap_init_module.register_init_command
        is bootstrap_module.register_init_command
    )


def test_bootstrap_module_keeps_init_defs_out_of_monolith() -> None:
    function_names = _bootstrap_function_names()

    assert "handle_init" not in function_names
    assert "register_init_command" not in function_names


def test_bootstrap_plan_module_exports_match_bootstrap_surface() -> None:
    assert bootstrap_plan_module.handle_plan is bootstrap_module.handle_plan
    assert (
        bootstrap_plan_module.register_plan_command
        is bootstrap_module.register_plan_command
    )


def test_bootstrap_module_keeps_plan_defs_out_of_monolith() -> None:
    function_names = _bootstrap_function_names()

    assert "handle_plan" not in function_names
    assert "register_plan_command" not in function_names
