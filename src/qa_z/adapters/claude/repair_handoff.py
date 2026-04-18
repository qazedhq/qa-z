"""Claude-facing rendering for normalized repair handoff packets."""

from __future__ import annotations

from qa_z.repair_handoff import RepairHandoffPacket, RepairTarget, ValidationCommand


def render_claude_handoff(handoff: RepairHandoffPacket) -> str:
    """Render an explanatory Claude repair prompt from a handoff packet."""
    lines = [
        "# QA-Z Claude Repair Handoff",
        "",
        "Analyze the QA-Z evidence, then make the smallest safe repair.",
        "Do not infer root causes beyond the provided findings and command evidence.",
        "",
        "## Context",
        "",
        f"- Source status: {handoff.provenance['source_status']}",
        f"- Source run: `{handoff.provenance['source_run_dir']}`",
        f"- Contract: `{handoff.provenance['contract_path']}`",
        f"- Fast summary: `{handoff.provenance['fast_summary_path']}`",
        "",
        "## What To Fix",
        "",
    ]
    if not handoff.targets:
        lines.extend(["No blocking repair targets were selected.", ""])
    for target in handoff.targets:
        lines.extend(render_target(target))

    lines.extend(render_list("## Affected Files", handoff.affected_files, code=True))
    lines.extend(render_list("## Constraints", handoff.constraints))
    lines.extend(render_list("## Non-Goals", handoff.non_goals))
    lines.extend(
        [
            "## Suggested Workflow",
            "",
            *[f"- {step}" for step in handoff.workflow_steps],
            "",
            "## Validation Commands",
            "",
        ]
    )
    lines.extend(
        render_validation_command(command) for command in handoff.validation_commands
    )
    lines.extend(["", "## Success Criteria", ""])
    lines.extend(f"- {item}" for item in handoff.success_criteria)
    return "\n".join(lines).strip() + "\n"


def render_target(target: RepairTarget) -> list[str]:
    """Render one Claude target."""
    lines = [
        f"### {target.title}",
        "",
        f"- Target id: `{target.id}`",
        f"- Source: {target.source}",
        f"- Severity: {target.severity}",
        f"- Repair objective: {target.objective}",
        f"- QA-Z rationale: {target.rationale}",
    ]
    if target.location:
        lines.append(f"- Location: `{target.location}`")
    if target.occurrences is not None:
        lines.append(f"- Occurrences: {target.occurrences}")
    if target.command:
        lines.append(f"- Local recheck: `{format_command(target.command)}`")
    if target.affected_files:
        lines.append(
            "- Affected files: "
            + ", ".join(f"`{path}`" for path in target.affected_files)
        )
    if target.evidence:
        lines.extend(["", "Evidence:", "```text", target.evidence.rstrip(), "```"])
    lines.append("")
    return lines


def render_validation_command(command: ValidationCommand) -> str:
    """Render one validation command."""
    return f"- `{format_command(command.command)}` - {command.success_criteria}"


def render_list(heading: str, items: list[str], *, code: bool = False) -> list[str]:
    """Render a Markdown list when items are present."""
    lines = [heading, ""]
    if not items:
        lines.extend(["- none", ""])
        return lines
    if code:
        lines.extend(f"- `{item}`" for item in items)
    else:
        lines.extend(f"- {item}" for item in items)
    lines.append("")
    return lines


def format_command(command: list[str]) -> str:
    """Render an argv list for Markdown."""
    return " ".join(command)
