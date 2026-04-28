"""Authoritative registry data for modular CLI commands."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Callable

from qa_z.commands.bootstrap import register_init_command, register_plan_command
from qa_z.commands.config_doctor import register_doctor_command
from qa_z.commands.execution import (
    register_deep_command,
    register_fast_command,
    register_repair_prompt_command,
)
from qa_z.commands.planning import (
    register_backlog_command,
    register_self_inspect_command,
    register_select_next_command,
)
from qa_z.commands.reviewing import (
    register_github_summary_command,
    register_review_command,
)
from qa_z.commands.runtime import (
    register_autonomy_command,
    register_benchmark_command,
    register_executor_bridge_command,
    register_executor_result_command,
)
from qa_z.commands.sessioning import (
    register_repair_session_command,
    register_verify_command,
)


@dataclass(frozen=True)
class CommandRegistrar:
    """Named command registration hook."""

    name: str
    register: Callable[[argparse._SubParsersAction], None]


COMMAND_REGISTRY_GROUPS = {
    "root": (
        CommandRegistrar(name="init", register=register_init_command),
        CommandRegistrar(name="doctor", register=register_doctor_command),
        CommandRegistrar(name="plan", register=register_plan_command),
        CommandRegistrar(name="review", register=register_review_command),
        CommandRegistrar(
            name="github-summary",
            register=register_github_summary_command,
        ),
    ),
    "execution": (
        CommandRegistrar(name="fast", register=register_fast_command),
        CommandRegistrar(name="deep", register=register_deep_command),
        CommandRegistrar(
            name="repair-prompt",
            register=register_repair_prompt_command,
        ),
    ),
    "session": (
        CommandRegistrar(name="verify", register=register_verify_command),
        CommandRegistrar(
            name="repair-session",
            register=register_repair_session_command,
        ),
    ),
    "planning": (
        CommandRegistrar(name="self-inspect", register=register_self_inspect_command),
        CommandRegistrar(name="select-next", register=register_select_next_command),
        CommandRegistrar(name="backlog", register=register_backlog_command),
    ),
    "runtime": (
        CommandRegistrar(name="autonomy", register=register_autonomy_command),
        CommandRegistrar(
            name="executor-bridge",
            register=register_executor_bridge_command,
        ),
        CommandRegistrar(
            name="executor-result",
            register=register_executor_result_command,
        ),
        CommandRegistrar(name="benchmark", register=register_benchmark_command),
    ),
}

ROOT_COMMAND_REGISTRARS = COMMAND_REGISTRY_GROUPS["root"]
EXECUTION_COMMAND_REGISTRARS = COMMAND_REGISTRY_GROUPS["execution"]
SESSION_COMMAND_REGISTRARS = COMMAND_REGISTRY_GROUPS["session"]
PLANNING_COMMAND_REGISTRARS = COMMAND_REGISTRY_GROUPS["planning"]
RUNTIME_COMMAND_REGISTRARS = COMMAND_REGISTRY_GROUPS["runtime"]

ALL_COMMAND_REGISTRARS = (
    *(
        registrar
        for registrars in COMMAND_REGISTRY_GROUPS.values()
        for registrar in registrars
    ),
)
