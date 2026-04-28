"""Executor-bridge rendering helpers."""

from __future__ import annotations

from typing import Any

from qa_z.executor_bridge_context import (
    bridge_action_context_inputs,
    bridge_missing_action_context_inputs,
)
from qa_z.executor_bridge_guides import bridge_placeholder_summary_guidance
from qa_z.executor_bridge_summary import bridge_safety_rule_count
from qa_z.executor_bridge_support import format_command
from qa_z.self_improvement import render_live_repository_summary


def render_executor_bridge_guide(
    manifest: dict[str, Any], handoff: dict[str, Any]
) -> str:
    """Render the human-readable bridge guide."""
    repair = handoff.get("repair") if isinstance(handoff, dict) else {}
    targets = repair.get("targets") if isinstance(repair, dict) else []
    objectives = repair.get("objectives") if isinstance(repair, dict) else []
    lines = [
        "# QA-Z External Executor Bridge",
        "",
        "This package gives an external human, Codex, or Claude executor the local QA-Z evidence needed for repair.",
        "QA-Z does not call live model APIs, edit code, schedule work, commit, push, or post GitHub comments.",
        "",
        "## Bridge",
        "",
        f"- Bridge id: `{manifest['bridge_id']}`",
        f"- Status: `{manifest['status']}`",
        f"- Source loop: `{manifest.get('source_loop_id') or 'none'}`",
        f"- Source session: `{manifest['source_session_id']}`",
        f"- Baseline run: `{manifest['baseline_run_dir']}`",
        "",
        "## Why This Work Was Selected",
        "",
    ]
    selected = manifest.get("selected_task_ids") or []
    if selected:
        lines.extend(f"- Selected task: `{item}`" for item in selected)
    else:
        lines.append("- Bridge was created directly from a repair session.")
    recommendations = manifest.get("evidence_summary", {}).get("why_selected", [])
    for recommendation in recommendations:
        lines.append(f"- Recommendation: {recommendation}")
    live_repository = manifest.get("live_repository")
    if isinstance(live_repository, dict):
        lines.extend(
            [
                "",
                "## Live Repository Context",
                "",
                f"- {render_live_repository_summary(live_repository)}",
            ]
        )
    lines.extend(["", "## What To Fix", ""])
    if isinstance(objectives, list) and objectives:
        lines.extend(f"- {objective}" for objective in objectives)
    elif isinstance(targets, list) and targets:
        lines.extend(
            f"- {target.get('objective')}"
            for target in targets
            if isinstance(target, dict)
        )
    else:
        lines.append(
            "- Use the packaged handoff artifacts to identify the repair target."
        )
    lines.extend(["", "## Where To Look", ""])
    lines.append(f"- Session manifest: `{manifest['inputs']['session']}`")
    lines.append(f"- Handoff JSON: `{manifest['inputs']['handoff']}`")
    lines.append(
        f"- Safety package: `{manifest['inputs']['executor_safety_markdown']}`"
    )
    if manifest["inputs"].get("autonomy_outcome"):
        lines.append(f"- Autonomy outcome: `{manifest['inputs']['autonomy_outcome']}`")
    action_context = bridge_action_context_inputs(manifest)
    if action_context:
        lines.append("- Action context:")
        lines.extend(
            f"  - `{item['copied_path']}` from `{item['source_path']}`"
            for item in action_context
        )
    missing_action_context = bridge_missing_action_context_inputs(manifest)
    if missing_action_context:
        lines.append("- Action context missing:")
        lines.extend(f"  - `{path}`" for path in missing_action_context)
    lines.append(
        "- Result template: "
        f"`{manifest['return_contract']['result_template_path']}` "
        f"-> create `{manifest['return_contract']['expected_result_artifact']}`"
    )
    lines.extend(["", "## Do Not Change", ""])
    lines.extend(f"- {item}" for item in manifest["non_goals"])
    lines.extend(["", "## Safety Package", ""])
    lines.append(f"- Policy JSON: `{manifest['safety_package']['policy_json']}`")
    lines.append(
        f"- Policy Markdown: `{manifest['safety_package']['policy_markdown']}`"
    )
    lines.append(f"- Safety rule count: `{bridge_safety_rule_count(manifest)}`")
    lines.extend(["", "## Validation", ""])
    for command in manifest["validation_commands"]:
        lines.append(f"- `{format_command(command)}`")
    lines.extend(
        [
            "",
            "## Return Contract",
            "",
            f"- Expected next step: {manifest['return_contract']['expected_next_step']}",
            "- Write an executor result JSON before re-entering QA-Z verification.",
            f"- Result template: `{manifest['return_contract']['result_template_path']}`",
            f"- Expected result artifact: `{manifest['return_contract']['expected_result_artifact']}`",
            f"- {bridge_placeholder_summary_guidance()}",
            "- Return control to QA-Z by running the validation command after edits.",
            "- If validation fails, preserve partial evidence and record what remains.",
            f"- Verify summary: `{manifest['return_contract']['expected_verify_artifacts']['summary_json']}`",
            f"- Verify compare: `{manifest['return_contract']['expected_verify_artifacts']['compare_json']}`",
            f"- Verify report: `{manifest['return_contract']['expected_verify_artifacts']['report_markdown']}`",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_bridge_stdout(manifest: dict[str, Any]) -> str:
    """Render human CLI output for bridge creation."""
    return_contract = manifest.get("return_contract")
    if not isinstance(return_contract, dict):
        return_contract = {}
    verify_command = return_contract.get("verify_command")
    lines = [
        "qa-z executor-bridge: ready_for_external_executor",
        f"Bridge: {manifest['bridge_dir']}",
        f"Source session: {manifest['source_session_id']}",
        f"Handoff: {manifest['handoff_path']}",
        f"Executor guide: {manifest['bridge_dir']}/executor_guide.md",
        f"Result template: {return_contract.get('result_template_path')}",
        f"Expected result: {return_contract.get('expected_result_artifact')}",
        "Template summary: replace placeholder before ingest",
        f"Safety package: {manifest['safety_package']['policy_markdown']}",
        f"Safety rule count: {bridge_safety_rule_count(manifest)}",
    ]
    live_repository = manifest.get("live_repository")
    if isinstance(live_repository, dict):
        lines.append(
            f"Live repository: {render_live_repository_summary(live_repository)}"
        )
    action_context = bridge_action_context_inputs(manifest)
    if action_context:
        lines.append(f"Action context inputs: {len(action_context)}")
    missing_action_context = bridge_missing_action_context_inputs(manifest)
    if missing_action_context:
        lines.append(
            "Missing action context: "
            f"{len(missing_action_context)} ({'; '.join(missing_action_context)})"
        )
    if isinstance(verify_command, list):
        lines.append(
            f"Verify command: {format_command([str(item) for item in verify_command])}"
        )
    return "\n".join(lines)
