"""Build deterministic agent repair prompts from QA-Z run artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    ContractContext,
    RunSource,
    format_path,
)
from qa_z.reporters.deep_context import build_deep_context
from qa_z.reporters.repair_prompt_artifacts import (
    repair_packet_json,
    write_repair_artifacts,
)
from qa_z.reporters.repair_prompt_failures import (
    default_failure_summary,
    extract_candidate_files,
    failure_context,
    fix_priority,
    ordered_candidate_files,
    sorted_failures,
)
from qa_z.reporters.repair_prompt_packet import build_repair_packet
from qa_z.reporters.repair_prompt_render import render_repair_prompt
from qa_z.reporters.repair_prompt_sections import (
    blocking_grouped_findings,
    blocking_severities,
    done_when_items,
    evidence_tail,
    format_command,
    format_grouped_finding,
    format_inline_code_list,
    format_list,
    format_severity_summary_dict,
    has_blocking_deep_findings,
    render_failure_markdown,
    render_optional_list,
    render_security_findings,
    suggested_fix_order,
    unique_preserve_order,
    utc_now,
)
from qa_z.runners.models import RunSummary

__all__ = [
    "DEFAULT_CONSTRAINTS",
    "DEFAULT_DONE_WHEN",
    "FailureContext",
    "PASSING_DONE_WHEN",
    "RepairPacket",
    "blocking_grouped_findings",
    "blocking_severities",
    "build_repair_packet",
    "default_failure_summary",
    "done_when_items",
    "evidence_tail",
    "extract_candidate_files",
    "failure_context",
    "fix_priority",
    "format_command",
    "format_grouped_finding",
    "format_inline_code_list",
    "format_list",
    "format_severity_summary_dict",
    "has_blocking_deep_findings",
    "ordered_candidate_files",
    "repair_packet_json",
    "render_failure_markdown",
    "render_optional_list",
    "render_repair_prompt",
    "render_security_findings",
    "sorted_failures",
    "suggested_fix_order",
    "unique_preserve_order",
    "utc_now",
    "write_repair_artifacts",
]

DEFAULT_CONSTRAINTS = [
    "Do not weaken tests.",
    "Do not remove lint/type checks to make the run pass.",
    "Preserve existing CLI flags and artifact names unless the contract explicitly changes them.",
]

DEFAULT_DONE_WHEN = [
    "qa-z fast exits with code 0",
    "All failed checks in this packet pass",
    "Documented CLI flags and artifact paths remain compatible",
]

PASSING_DONE_WHEN = ["No repair required; source run already passed"]


@dataclass
class FailureContext:
    """Repair-ready context for one failed check."""

    id: str
    kind: str
    tool: str
    command: list[str]
    exit_code: int | None
    duration_ms: int
    summary: str
    stdout_tail: str
    stderr_tail: str
    candidate_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Render this failure context as JSON-safe data."""
        return {
            "id": self.id,
            "kind": self.kind,
            "tool": self.tool,
            "command": self.command,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "summary": self.summary,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
            "candidate_files": self.candidate_files,
        }


@dataclass
class RepairPacket:
    """Deterministic packet for feeding failed QA-Z runs back to an agent."""

    version: int
    generated_at: str
    repair_needed: bool
    run: dict[str, Any]
    contract: dict[str, Any]
    failures: list[FailureContext]
    suggested_fix_order: list[str]
    done_when: list[str]
    agent_prompt: str
    deep: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Render this repair packet as JSON-safe data."""
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "repair_needed": self.repair_needed,
            "run": self.run,
            "contract": self.contract,
            "failures": [failure.to_dict() for failure in self.failures],
            "suggested_fix_order": self.suggested_fix_order,
            "done_when": self.done_when,
            "agent_prompt": self.agent_prompt,
            "deep": self.deep,
        }


def _build_repair_packet_impl(
    *,
    summary: RunSummary,
    run_source: RunSource,
    contract: ContractContext,
    root: Path,
    deep_summary: RunSummary | None = None,
) -> RepairPacket:
    """Build a repair packet from a run summary and contract."""
    failures = sorted_failures(summary, contract)
    deep_context = build_deep_context(deep_summary)
    repair_needed = bool(failures) or has_blocking_deep_findings(deep_context)
    done_when = done_when_items(repair_needed, deep_context)
    run_context: dict[str, Any] = {
        "dir": format_path(run_source.run_dir, root),
        "status": summary.status,
        "contract_path": summary.contract_path,
        "started_at": summary.started_at,
        "finished_at": summary.finished_at,
    }
    if summary.selection is not None:
        run_context["selection"] = summary.selection.to_dict()
    contract_context = {
        "path": contract.path,
        "title": contract.title,
        "summary": contract.summary,
        "scope_items": contract.scope_items,
        "acceptance_checks": contract.acceptance_checks,
        "constraints": contract.constraints,
    }
    packet = RepairPacket(
        version=1,
        generated_at=utc_now(),
        repair_needed=repair_needed,
        run=run_context,
        contract=contract_context,
        failures=failures,
        suggested_fix_order=suggested_fix_order(failures, deep_context),
        done_when=done_when,
        agent_prompt="",
        deep=deep_context.to_dict() if deep_context else None,
    )
    packet.agent_prompt = render_repair_prompt(packet)
    return packet


def _render_repair_prompt_impl(packet: RepairPacket) -> str:
    """Render a Markdown prompt that can be pasted into a coding agent."""
    lines = [
        "# QA-Z Repair Prompt",
        "",
        "You are repairing a repository change that failed QA-Z checks.",
        "Make the minimum safe change required to satisfy the contract and pass the checks.",
        "",
        "## Goal",
        "",
        "Bring this change back to green without weakening tests, lint rules, type checks, or documented behavior.",
        "",
        "## Run Context",
        "",
        f"- Run status: {packet.run['status']}",
        f"- Run directory: `{packet.run['dir']}`",
        f"- Contract: `{packet.contract['path']}`",
        "",
        "## Contract Summary",
        "",
        packet.contract.get("summary") or "No contract summary available.",
        "",
    ]
    selection = packet.run.get("selection")
    if isinstance(selection, dict):
        lines.extend(
            [
                "### Check Selection",
                "",
                f"- Mode: {selection.get('mode', 'unknown')}",
                f"- Input source: {selection.get('input_source', 'none')}",
                f"- Full checks: {format_list(selection.get('full_checks', []))}",
                f"- Targeted checks: {format_list(selection.get('targeted_checks', []))}",
                f"- Skipped checks: {format_list(selection.get('skipped_checks', []))}",
                "",
            ]
        )
    lines.extend(render_optional_list("### Scope", packet.contract["scope_items"]))
    lines.extend(
        render_optional_list(
            "### Acceptance Checks", packet.contract["acceptance_checks"]
        )
    )
    lines.extend(render_security_findings(packet.deep))
    lines.extend(["## Failing Checks", ""])
    if not packet.failures:
        lines.extend(["No failing checks were found for this run.", ""])
    for failure in packet.failures:
        lines.extend(render_failure_markdown(failure))

    constraints = unique_preserve_order(
        [*packet.contract.get("constraints", []), *DEFAULT_CONSTRAINTS]
    )
    lines.extend(render_optional_list("## Constraints", constraints, bullet="*"))
    lines.extend(
        [
            "## Suggested Fix Order",
            "",
            "1. Fix formatting issues first if present.",
            "2. Fix lint findings next.",
            "3. Fix type errors.",
            "4. Fix failing tests last and re-run the full fast suite.",
            "",
            "## Done When",
            "",
        ]
    )
    lines.extend(
        f"* `{item}`" if item.startswith("qa-z ") else f"* {item}"
        for item in packet.done_when
    )
    return "\n".join(lines).strip() + "\n"


def _write_repair_artifacts_impl(
    packet: RepairPacket, output_dir: Path
) -> tuple[Path, Path]:
    """Write packet.json and prompt.md artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    packet_path = output_dir / "packet.json"
    prompt_path = output_dir / "prompt.md"
    packet_path.write_text(
        json.dumps(packet.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    prompt_path.write_text(packet.agent_prompt, encoding="utf-8")
    return packet_path, prompt_path


def _repair_packet_json_impl(packet: RepairPacket) -> str:
    """Render a repair packet as JSON for stdout."""
    return json.dumps(packet.to_dict(), indent=2, sort_keys=True) + "\n"
