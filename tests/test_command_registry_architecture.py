"""Architecture tests for command registry seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import pytest

import qa_z.commands as commands_module
import qa_z.commands.command_registration as command_registration_module
import qa_z.commands.command_registry as command_registry_module


def _commands_function_names() -> set[str]:
    source = Path(commands_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(commands_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_command_registry_module_exports_match_commands_surface() -> None:
    assert command_registry_module.CommandRegistrar is commands_module.CommandRegistrar
    assert (
        command_registry_module.COMMAND_REGISTRY_GROUPS
        is commands_module.COMMAND_REGISTRY_GROUPS
    )
    assert (
        command_registry_module.ALL_COMMAND_REGISTRARS
        is commands_module.ALL_COMMAND_REGISTRARS
    )


def test_command_registration_module_exports_match_commands_surface() -> None:
    assert (
        command_registration_module.register_command_group
        is commands_module.register_command_group
    )
    assert (
        command_registration_module.register_root_commands
        is commands_module.register_root_commands
    )
    assert (
        command_registration_module.register_execution_commands
        is commands_module.register_execution_commands
    )
    assert (
        command_registration_module.register_session_commands
        is commands_module.register_session_commands
    )
    assert (
        command_registration_module.register_planning_commands
        is commands_module.register_planning_commands
    )
    assert (
        command_registration_module.register_modular_commands
        is commands_module.register_modular_commands
    )


def test_commands_module_keeps_registration_defs_out_of_monolith() -> None:
    function_names = _commands_function_names()

    assert "register_command_group" not in function_names
    assert "register_root_commands" not in function_names
    assert "register_execution_commands" not in function_names
    assert "register_session_commands" not in function_names
    assert "register_planning_commands" not in function_names
    assert "register_modular_commands" not in function_names


def test_register_command_group_rejects_unknown_group_name() -> None:
    with pytest.raises(ValueError, match="unknown command group"):
        command_registration_module.register_command_group(
            subparsers=None,  # type: ignore[arg-type]
            group_name="unknown",
        )
