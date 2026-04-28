"""Runtime-oriented CLI commands that remain local and deterministic."""

from __future__ import annotations

from qa_z.commands.runtime_autonomy import (
    handle_autonomy,
    register_autonomy_command,
)
from qa_z.commands.runtime_benchmark import (
    handle_benchmark,
    register_benchmark_command,
)
from qa_z.commands.runtime_bridge import (
    handle_executor_bridge,
    register_executor_bridge_command,
)
from qa_z.commands.runtime_executor_result import (
    dry_run_action_summaries,
    dry_run_rule_counts,
    dry_run_text_field,
    handle_executor_result_dry_run,
    handle_executor_result_ingest,
    register_executor_result_command,
    render_executor_result_dry_run_stdout,
)

__all__ = [
    "dry_run_action_summaries",
    "dry_run_rule_counts",
    "dry_run_text_field",
    "handle_autonomy",
    "handle_benchmark",
    "handle_executor_bridge",
    "handle_executor_result_dry_run",
    "handle_executor_result_ingest",
    "register_autonomy_command",
    "register_benchmark_command",
    "register_executor_bridge_command",
    "register_executor_result_command",
    "render_executor_result_dry_run_stdout",
]
