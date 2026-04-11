"""Build deterministic agent repair prompts from QA-Z run artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    ContractContext,
    RunSource,
    extract_candidate_files,
    extract_contract_candidate_files,
    format_path,
)
from qa_z.runners.models import CheckResult, RunSummary

FIX_KIND_PRIORITY = {
    "format": 0,
    "lint": 1,
    "typecheck": 2,
    "test": 3,
}

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
        }


def build_repair_packet(
    *,
    summary: RunSummary,
    run_source: RunSource,
    contract: ContractContext,
    root: Path,
) -> RepairPacket:
    """Build a repair packet from a run summary and contract."""
    failures = sorted_failures(summary, contract)
    repair_needed = bool(failures)
    done_when = DEFAULT_DONE_WHEN if repair_needed else PASSING_DONE_WHEN
    run_context = {
        "dir": format_path(run_source.run_dir, root),
        "status": summary.status,
        "contract_path": summary.contract_path,
        "started_at": summary.started_at,
        "finished_at": summary.finished_at,
    }
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
        suggested_fix_order=[failure.id for failure in failures],
        done_when=done_when,
        agent_prompt="",
    )
    packet.agent_prompt = render_repair_prompt(packet)
    return packet


def sorted_failures(
    summary: RunSummary, contract: ContractContext
) -> list[FailureContext]:
    """Return failed or errored checks in deterministic repair order."""
    contract_candidates = extract_contract_candidate_files(contract)
    failure_checks = [
        check for check in summary.checks if check.status in {"failed", "error"}
    ]
    ordered_checks = sorted(
        enumerate(failure_checks),
        key=lambda item: (fix_priority(item[1]), item[0], item[1].id),
    )
    return [
        failure_context(check, contract_candidates) for _index, check in ordered_checks
    ]


def failure_context(
    check: CheckResult, contract_candidates: list[str]
) -> FailureContext:
    """Build repair context for one check result."""
    evidence = "\n".join(
        part for part in (check.stdout_tail, check.stderr_tail) if part
    )
    output_candidates = extract_candidate_files(evidence)
    candidate_files = ordered_candidate_files(contract_candidates, output_candidates)
    return FailureContext(
        id=check.id,
        kind=check.kind,
        tool=check.tool,
        command=check.command,
        exit_code=check.exit_code,
        duration_ms=check.duration_ms,
        summary=check.message or default_failure_summary(check),
        stdout_tail=check.stdout_tail,
        stderr_tail=check.stderr_tail,
        candidate_files=candidate_files,
    )


def ordered_candidate_files(
    contract_candidates: list[str], output_candidates: list[str]
) -> list[str]:
    """Merge candidate files with contract hints first, capped at ten files."""
    merged: list[str] = []
    for path in [*contract_candidates, *output_candidates]:
        if path not in merged:
            merged.append(path)
    return merged[:10]


def default_failure_summary(check: CheckResult) -> str:
    """Render a compact deterministic failure summary."""
    if check.exit_code is None:
        return f"{check.tool} did not complete successfully."
    return f"{check.tool} exited with code {check.exit_code}."


def fix_priority(check: CheckResult | FailureContext) -> int:
    """Return deterministic repair priority for a check."""
    kind_priority = FIX_KIND_PRIORITY.get(check.kind)
    if kind_priority is not None:
        return kind_priority
    lowered = check.id.lower()
    for kind, priority in FIX_KIND_PRIORITY.items():
        if kind in lowered:
            return priority
    return len(FIX_KIND_PRIORITY)


def render_repair_prompt(packet: RepairPacket) -> str:
    """Render a Markdown prompt that can be pasted into a coding agent."""
    lines = [
        "# QA-Z Repair Prompt",
        "",
        "You are repairing a repository change that failed QA-Z fast checks.",
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
    lines.extend(render_optional_list("### Scope", packet.contract["scope_items"]))
    lines.extend(
        render_optional_list(
            "### Acceptance Checks", packet.contract["acceptance_checks"]
        )
    )
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


def render_optional_list(
    heading: str, items: list[str], *, bullet: str = "-"
) -> list[str]:
    """Render a markdown heading and list when items exist."""
    if not items:
        return []
    return [heading, "", *[f"{bullet} {item}" for item in items], ""]


def render_failure_markdown(failure: FailureContext) -> list[str]:
    """Render one failed check for the repair prompt."""
    lines = [
        f"### {failure.id}",
        "",
        f"- Tool: {failure.tool}",
        f"- Command: `{format_command(failure.command)}`",
        f"- Exit code: `{failure.exit_code}`",
    ]
    if failure.candidate_files:
        lines.extend(["- Candidate files:"])
        lines.extend(f"  - `{path}`" for path in failure.candidate_files)
    lines.extend(["", "Evidence:", "```text", evidence_tail(failure), "```", ""])
    return lines


def evidence_tail(failure: FailureContext) -> str:
    """Combine stdout and stderr tail for markdown evidence."""
    parts = []
    if failure.stdout_tail:
        parts.append(failure.stdout_tail.rstrip())
    if failure.stderr_tail:
        parts.append(failure.stderr_tail.rstrip())
    return "\n".join(parts) if parts else "No stdout or stderr tail captured."


def write_repair_artifacts(packet: RepairPacket, output_dir: Path) -> tuple[Path, Path]:
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


def repair_packet_json(packet: RepairPacket) -> str:
    """Render a repair packet as JSON for stdout."""
    return json.dumps(packet.to_dict(), indent=2, sort_keys=True) + "\n"


def format_command(command: list[str]) -> str:
    """Render a subprocess command for human-readable markdown."""
    return " ".join(command)


def unique_preserve_order(items: list[str]) -> list[str]:
    """Return unique non-empty items in first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        normalized = item.strip()
        key = normalized.rstrip(".")
        if normalized and key not in seen:
            seen.add(key)
            result.append(normalized)
    return result


def utc_now() -> str:
    """Return an ISO-like UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
