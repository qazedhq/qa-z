"""Guide helpers for executor-bridge human-facing surfaces."""

from __future__ import annotations

from typing import Any

from qa_z.executor_result import PLACEHOLDER_SUMMARY
from qa_z.self_improvement import render_live_repository_summary


def bridge_placeholder_summary_guidance() -> str:
    """Return stable guidance for completing result templates."""
    return f"Replace the placeholder summary before ingest: `{PLACEHOLDER_SUMMARY}`"


def render_executor_specific_guide(manifest: dict[str, Any], executor: str) -> str:
    """Render a bridge-specific Codex or Claude guide."""
    lines = [
        f"# QA-Z Executor Bridge for {executor}",
        "",
        f"- Bridge id: `{manifest['bridge_id']}`",
        f"- Source session: `{manifest['source_session_id']}`",
        f"- Baseline run: `{manifest['baseline_run_dir']}`",
        f"- Handoff JSON: `{manifest['inputs']['handoff']}`",
        f"- Safety package: `{manifest['safety_package']['policy_markdown']}`",
        f"- Safety rule count: `{bridge_safety_rule_count(manifest)}`",
        "",
        "Use the packaged handoff and session evidence to make the smallest safe repair.",
        "Do not call Codex or Claude APIs from QA-Z.",
        "",
    ]
    live_repository = manifest.get("live_repository")
    if isinstance(live_repository, dict):
        lines.extend(
            [
                "## Live Repository Context",
                "",
                f"- Live repository: {render_live_repository_summary(live_repository)}",
                "",
            ]
        )
    warnings = manifest.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(["## Warnings", ""])
        for warning in warnings:
            if not isinstance(warning, dict):
                continue
            warning_id = str(warning.get("id") or "warning")
            message = str(warning.get("message") or "").strip()
            if message:
                lines.append(f"- `{warning_id}`: {message}")
            else:
                lines.append(f"- `{warning_id}`")
        lines.append("")
    action_context = bridge_action_context_inputs(manifest)
    if action_context:
        lines.extend(["## Action Context", ""])
        lines.extend(
            f"- `{item['copied_path']}` from `{item['source_path']}`"
            for item in action_context
        )
        lines.append("")
    missing_action_context = bridge_missing_action_context_inputs(manifest)
    if missing_action_context:
        lines.extend(["## Action context missing", ""])
        lines.extend(f"- `{path}`" for path in missing_action_context)
        lines.append("")
    lines.extend(["## Safety", ""])
    lines.extend(f"- {item}" for item in manifest["non_goals"])
    objective_lines = [
        str(item).strip()
        for item in manifest.get("objectives", [])
        if str(item).strip()
    ]
    if objective_lines:
        lines.extend(["", "## What To Fix", ""])
        lines.extend(f"- {item}" for item in objective_lines)
    lines.extend(["", "## Validation", ""])
    for command in manifest["validation_commands"]:
        lines.append(f"- `{format_command(command)}`")
    lines.extend(["", "## Return Contract", ""])
    lines.append(f"- {manifest['return_contract']['expected_next_step']}")
    lines.append(f"- {bridge_placeholder_summary_guidance()}")
    lines.append("- Preserve partial completion evidence if the command fails.")
    return "\n".join(lines).strip() + "\n"


from qa_z.executor_bridge_context import (  # noqa: E402
    bridge_action_context_inputs,
    bridge_missing_action_context_inputs,
)
from qa_z.executor_bridge_summary import bridge_safety_rule_count  # noqa: E402
from qa_z.executor_bridge_support import format_command  # noqa: E402
