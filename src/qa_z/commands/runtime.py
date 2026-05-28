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
from qa_z.commands.runtime_governance import (
    handle_baseline_create,
    handle_governance_report,
    handle_waiver_add,
    register_baseline_command,
    register_governance_command,
    register_waiver_command,
)
from qa_z.commands.runtime_policy import (
    handle_policy_validate,
    register_policy_command,
    render_policy_validation_text,
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
from qa_z.commands.runtime_scorecard import (
    handle_scorecard,
    register_scorecard_command,
    render_scorecard_markdown,
    render_scorecard_text,
)

__all__ = [
    "dry_run_action_summaries",
    "dry_run_rule_counts",
    "dry_run_text_field",
    "handle_autonomy",
    "handle_baseline_create",
    "handle_benchmark",
    "handle_executor_bridge",
    "handle_executor_result_dry_run",
    "handle_executor_result_ingest",
    "handle_governance_report",
    "handle_policy_validate",
    "handle_scorecard",
    "handle_waiver_add",
    "register_autonomy_command",
    "register_baseline_command",
    "register_benchmark_command",
    "register_executor_bridge_command",
    "register_executor_result_command",
    "register_governance_command",
    "register_policy_command",
    "register_scorecard_command",
    "register_waiver_command",
    "render_executor_result_dry_run_stdout",
    "render_policy_validation_text",
    "render_scorecard_markdown",
    "render_scorecard_text",
]
