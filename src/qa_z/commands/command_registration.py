"""Helpers that register modular CLI command groups."""

from __future__ import annotations

import argparse

from qa_z.commands.command_registry import (
    ALL_COMMAND_REGISTRARS,
    COMMAND_REGISTRY_GROUPS,
)


def register_command_group(
    subparsers: argparse._SubParsersAction, group_name: str
) -> None:
    """Register one modular command group on the CLI parser."""
    if group_name not in COMMAND_REGISTRY_GROUPS:
        raise ValueError(f"unknown command group: {group_name}")
    for registrar in COMMAND_REGISTRY_GROUPS[group_name]:
        registrar.register(subparsers)


def register_root_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register modular root commands on the CLI parser."""
    register_command_group(subparsers, "root")


def register_execution_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register modular execution commands on the CLI parser."""
    register_command_group(subparsers, "execution")


def register_session_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register modular verification and session commands on the CLI parser."""
    register_command_group(subparsers, "session")


def register_planning_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register modular planning commands on the CLI parser."""
    register_command_group(subparsers, "planning")


def register_modular_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register every modular root command on the CLI parser."""
    for registrar in ALL_COMMAND_REGISTRARS:
        registrar.register(subparsers)
