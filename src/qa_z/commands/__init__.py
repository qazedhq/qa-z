"""Registry surface for modular CLI command registration."""

from __future__ import annotations

from qa_z.commands.command_registration import (
    register_command_group,
    register_execution_commands,
    register_modular_commands,
    register_planning_commands,
    register_root_commands,
    register_session_commands,
)
from qa_z.commands.command_registry import (
    ALL_COMMAND_REGISTRARS,
    COMMAND_REGISTRY_GROUPS,
    EXECUTION_COMMAND_REGISTRARS,
    PLANNING_COMMAND_REGISTRARS,
    ROOT_COMMAND_REGISTRARS,
    RUNTIME_COMMAND_REGISTRARS,
    SESSION_COMMAND_REGISTRARS,
    CommandRegistrar,
)

__all__ = [
    "ALL_COMMAND_REGISTRARS",
    "COMMAND_REGISTRY_GROUPS",
    "EXECUTION_COMMAND_REGISTRARS",
    "PLANNING_COMMAND_REGISTRARS",
    "ROOT_COMMAND_REGISTRARS",
    "RUNTIME_COMMAND_REGISTRARS",
    "SESSION_COMMAND_REGISTRARS",
    "CommandRegistrar",
    "register_command_group",
    "register_execution_commands",
    "register_modular_commands",
    "register_planning_commands",
    "register_root_commands",
    "register_session_commands",
]
