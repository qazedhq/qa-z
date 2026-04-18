"""Codex-facing rendering for normalized repair handoff packets."""

from __future__ import annotations

from qa_z.repair_handoff import RepairHandoffPacket, RepairTarget, ValidationCommand


def render_codex_handoff(handoff: RepairHandoffPacket) -> str:
    """Render a concise Codex execution prompt from a handoff packet."""
    lines = [
        "# QA-Z Codex Repair Handoff",
        "",
        "Implement the repair now.",
        "Use only the QA-Z evidence in this packet. Keep the diff focused.",
        "",
        "## Run",
        "",
        f"- Status: {handoff.provenance['source_status']}",
        f"- Run: `{handoff.provenance['source_run_dir']}`",
        f"- Fast summary: `{handoff.provenance['fast_summary_path']}`",
        f"- Contract: `{handoff.provenance['contract_path']}`",
        "",
        "## Repair Targets",
        "",
    ]
    if not handoff.targets:
        lines.extend(["No blocking repair targets were selected.", ""])
    for index, target in enumerate(handoff.targets, start=1):
        lines.extend(render_target(index, target))

    lines.extend(render_list("## Affected Files", handoff.affected_files, code=True))
    lines.extend(render_list("## Constraints", handoff.constraints))
    lines.extend(render_list("## Non-Goals", handoff.non_goals))
    lines.extend(["## Validation Commands", ""])
    lines.extend(
        render_validation_command(command) for command in handoff.validation_commands
    )
    lines.extend(["", "## Success Criteria", ""])
    lines.extend(f"- {item}" for item in handoff.success_criteria)
    return "\n".join(lines).strip() + "\n"


def render_target(index: int, target: RepairTarget) -> list[str]:
    """Render one Codex target."""
    lines = [
        f"### {index}. {target.id}",
        "",
        f"- Source: {target.source}",
        f"- Severity: {target.severity}",
        f"- Objective: {target.objective}",
        f"- Rationale: {target.rationale}",
    ]
    if target.location:
        lines.append(f"- Location: `{target.location}`")
    if target.occurrences is not None:
        lines.append(f"- Occurrences: {target.occurrences}")
    if target.command:
        lines.append(f"- Recheck: `{format_command(target.command)}`")
    if target.affected_files:
        lines.append(
            "- Files: " + ", ".join(f"`{path}`" for path in target.affected_files)
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
