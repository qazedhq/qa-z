"""Execution-oriented CLI command surface."""

from __future__ import annotations

from qa_z.commands.execution_repair import (
    handle_repair_prompt,
    register_repair_prompt_command,
)
from qa_z.commands.execution_runs import (
    handle_deep,
    handle_fast,
    register_deep_command,
    register_fast_command,
    render_deep_stdout,
    render_fast_stdout,
    resolve_deep_selection_mode,
    resolve_fast_selection_mode,
)

__all__ = [
    "handle_deep",
    "handle_fast",
    "handle_repair_prompt",
    "register_deep_command",
    "register_fast_command",
    "register_repair_prompt_command",
    "render_deep_stdout",
    "render_fast_stdout",
    "resolve_deep_selection_mode",
    "resolve_fast_selection_mode",
]
