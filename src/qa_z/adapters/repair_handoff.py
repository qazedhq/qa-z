"""Deterministic repair handoff renderers for coding-agent adapters."""

from __future__ import annotations

from dataclasses import dataclass

from qa_z.repair_handoff import RepairHandoffPacket, RepairTarget, ValidationCommand

SUPPORTED_REPAIR_ADAPTERS = (
    "codex",
    "claude",
    "cursor",
    "aider",
    "openhands",
    "generic",
    "human",
)


@dataclass(frozen=True)
class AdapterProfile:
    """Prompt style and reporting expectations for one adapter."""

    name: str
    label: str
    opening: str
    style: str
    command_expectation: str
    reporting_expectations: tuple[str, ...]


ADAPTER_PROFILES: dict[str, AdapterProfile] = {
    "codex": AdapterProfile(
        name="codex",
        label="Codex",
        opening="Implement the repair now.",
        style="Work in a tight loop: inspect evidence, patch the smallest scope, run validation, then report evidence.",
        command_expectation="Run commands directly in the workspace and report exact outcomes.",
        reporting_expectations=(
            "Summary of the repair",
            "Files changed",
            "Validation commands and results",
            "Remaining risk or blockers",
        ),
    ),
    "claude": AdapterProfile(
        name="claude",
        label="Claude Code",
        opening="Analyze the QA-Z evidence, then make the smallest safe repair.",
        style="Explain assumptions briefly before editing, but keep the final change focused on the listed repair targets.",
        command_expectation="Use the listed validation commands as the source of truth, not conversational confidence.",
        reporting_expectations=(
            "What QA-Z evidence was addressed",
            "Files changed",
            "Validation commands and results",
            "Open questions or blockers",
        ),
    ),
    "cursor": AdapterProfile(
        name="cursor",
        label="Cursor",
        opening="Use the workspace context to repair only the QA-Z targets.",
        style="Prefer targeted edits in the listed files and avoid broad AI rewrite suggestions.",
        command_expectation="Run validation in the integrated terminal and keep terminal output tied to the QA-Z targets.",
        reporting_expectations=(
            "Changed files",
            "Risk fixed",
            "Validation commands and results",
            "Suggested next command",
        ),
    ),
    "aider": AdapterProfile(
        name="aider",
        label="aider",
        opening="Use this as the constrained edit request for aider.",
        style="Treat affected files as the initial edit set and ask before widening scope.",
        command_expectation="Run the required checks after edits and include the command results in the response.",
        reporting_expectations=(
            "Files edited",
            "Patch intent",
            "Validation commands and results",
            "Whether QA-Z verify was run",
        ),
    ),
    "openhands": AdapterProfile(
        name="openhands",
        label="OpenHands",
        opening="Execute the repair as a bounded task, then stop for QA-Z verification.",
        style="Plan briefly, patch only the evidence-backed target, avoid background services, and do not continue after validation failure without reporting it.",
        command_expectation="Run validation in the task environment and preserve artifact paths in the final report.",
        reporting_expectations=(
            "Plan executed",
            "Files changed",
            "Validation commands and results",
            "Artifacts or blockers",
        ),
    ),
    "generic": AdapterProfile(
        name="generic",
        label="Generic",
        opening="Use this as a human-readable repair checklist.",
        style="A human reviewer or any coding tool can follow this prompt without vendor-specific assumptions.",
        command_expectation="Run the commands locally and compare the result against the QA-Z success criteria.",
        reporting_expectations=(
            "Decision",
            "Files changed",
            "Validation commands and results",
            "Evidence paths reviewed",
        ),
    ),
    "human": AdapterProfile(
        name="human",
        label="Human Reviewer",
        opening="Use this as a human review checklist before merging.",
        style="Review the evidence-backed target, apply only the scoped repair, and keep the QA-Z verification command as the acceptance gate.",
        command_expectation="Run the listed commands locally and record the result in the review notes.",
        reporting_expectations=(
            "Decision",
            "Files reviewed or changed",
            "Validation commands and results",
            "Waiver or follow-up needed",
        ),
    ),
}


def render_repair_handoff_for_adapter(
    adapter: str, handoff: RepairHandoffPacket
) -> str:
    """Render an adapter-specific repair handoff prompt."""
    normalized = adapter.lower().strip()
    try:
        profile = ADAPTER_PROFILES[normalized]
    except KeyError as exc:
        supported = ", ".join(SUPPORTED_REPAIR_ADAPTERS)
        raise ValueError(
            f"unknown repair adapter '{adapter}'. Supported adapters: {supported}"
        ) from exc
    return render_profile_handoff(profile, handoff)


def render_all_repair_handoffs(handoff: RepairHandoffPacket) -> dict[str, str]:
    """Render every supported adapter handoff."""
    return {
        adapter: render_repair_handoff_for_adapter(adapter, handoff)
        for adapter in SUPPORTED_REPAIR_ADAPTERS
    }


def render_profile_handoff(
    profile: AdapterProfile, handoff: RepairHandoffPacket
) -> str:
    """Render a deterministic prompt using a shared merge-safety contract."""
    verify_command = f"qa-z verify --from-run {handoff.provenance['source_run_dir']}"
    lines = [
        f"# QA-Z {profile.label} Repair Handoff",
        "",
        profile.opening,
        profile.style,
        "",
        "## Objective",
        "",
        objective_text(handoff),
        "",
        "## Relevant Evidence",
        "",
        f"- Source status: {handoff.provenance['source_status']}",
        f"- Source run: `{handoff.provenance['source_run_dir']}`",
        f"- Fast summary: `{handoff.provenance['fast_summary_path']}`",
        f"- Contract: `{handoff.provenance['contract_path']}`",
    ]
    deep_summary_path = handoff.provenance.get("deep_summary_path")
    if deep_summary_path:
        lines.append(f"- Deep summary: `{deep_summary_path}`")
    lines.extend(
        [
            "",
            "## Repair Targets",
            "",
        ]
    )
    if not handoff.targets:
        lines.extend(["No blocking repair targets were selected.", ""])
    for index, target in enumerate(handoff.targets, start=1):
        lines.extend(render_target(index, target))

    lines.extend(render_files_and_risks(handoff))
    lines.extend(render_list("## Affected Files", handoff.affected_files, code=True))
    lines.extend(render_list("## Constraints", handoff.constraints))
    forbidden_actions = [
        "Do not weaken, delete, or skip tests to make QA-Z pass.",
        "Do not disable QA-Z checks, Semgrep rules, lint, or type checks unless the contract explicitly permits it.",
        "Do not widen the diff beyond the evidence-backed repair scope without reporting why.",
        "Do not call external AI APIs, services, deployment systems, or registries from this handoff.",
        "Do not claim success without validation.",
    ]
    lines.extend(render_list("## Forbidden Actions", forbidden_actions))
    lines.extend(render_list("## Forbidden Shortcuts", forbidden_actions))
    lines.extend(render_list("## Non-Goals", handoff.non_goals))
    lines.extend(
        [
            "## Required Validation",
            "",
            profile.command_expectation,
            f"After applying the fix, run `{verify_command}`.",
            "Do not claim success without validation.",
            "",
            "## Validation Commands",
            "",
        ]
    )
    lines.extend(
        render_validation_command(command) for command in handoff.validation_commands
    )
    lines.extend(["", "## Repair -> Verify Loop", ""])
    lines.extend(f"- {step}" for step in handoff.workflow_steps)
    lines.append(f"- After applying the fix, run `{verify_command}`.")
    lines.extend(
        [
            "",
            "## Final Report Format",
            "",
            "Return a concise completion report with:",
        ]
    )
    lines.extend(f"- {item}" for item in profile.reporting_expectations)
    lines.extend(
        [
            "",
            "## Merge-Safety Boundaries",
            "",
            "- QA-Z is the merge-safety layer; the coding tool is only the repair executor.",
            "- Treat QA-Z evidence and validation commands as authoritative over model confidence.",
            "- Do not merge, approve, or describe the repair as improved until QA-Z validation and verify evidence support it.",
            "",
            "## Success Criteria",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in handoff.success_criteria)
    return "\n".join(lines).strip() + "\n"


def objective_text(handoff: RepairHandoffPacket) -> str:
    """Render a compact objective for this repair handoff."""
    if not handoff.repair_needed:
        return "No repair is required; preserve the passing state and do not edit."
    if not handoff.repair_objectives:
        return "Investigate the QA-Z repair-needed state and regenerate evidence."
    return " ".join(handoff.repair_objectives)


def render_target(index: int, target: RepairTarget) -> list[str]:
    """Render one repair target."""
    lines = [
        f"### {index}. {target.id}",
        "",
        f"- Title: {target.title}",
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


def render_files_and_risks(handoff: RepairHandoffPacket) -> list[str]:
    """Render affected files and blocking risks together."""
    lines = ["## Files and Risks", ""]
    if not handoff.targets:
        lines.extend(["- No blocking risks selected.", ""])
        return lines
    for target in handoff.targets:
        files = ", ".join(f"`{path}`" for path in target.affected_files) or "none"
        lines.append(f"- `{target.id}` ({target.severity}): {files}")
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
