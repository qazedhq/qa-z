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
from qa_z.reporters.deep_context import (
    DeepContext,
    build_deep_context,
    format_finding_location,
    format_severity_summary,
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


def build_repair_packet(
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


def render_security_findings(deep: dict[str, Any] | None) -> list[str]:
    """Render Semgrep findings for repair prompts."""
    if not isinstance(deep, dict):
        return []

    grouped_findings = blocking_grouped_findings(deep)
    if grouped_findings:
        lines = [
            "## Deep QA Findings",
            "",
            "The following Semgrep findings must be addressed:",
            "",
        ]
        for finding in grouped_findings:
            lines.append(format_grouped_finding(finding))
        lines.extend(
            [
                "",
                "### Deep QA Completion Criteria",
                "",
                "- `qa-z deep` exits successfully",
                "- no blocking findings remain",
                "- fast checks remain green",
                "",
            ]
        )
        return lines

    findings = deep.get("top_findings")
    if not isinstance(findings, list) or not findings:
        return []

    lines = [
        "## Security Findings (Semgrep)",
        "",
        f"- Findings: {deep.get('findings_count', 0)}",
        f"- Highest severity: {deep.get('highest_severity') or 'none'}",
        f"- Severity summary: {format_severity_summary_dict(deep.get('severity_summary'))}",
        f"- Affected files: {format_inline_code_list(deep.get('affected_files'))}",
        "",
    ]
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        lines.append(
            "- "
            f"`{format_finding_location(finding)}` "
            f"{finding.get('severity', 'UNKNOWN')} "
            f"{finding.get('rule_id', 'unknown')} - "
            f"{finding.get('message', '')}"
        )
    lines.extend(
        [
            "",
            "Repair these findings without weakening fast checks, tests, or documented behavior.",
            "",
        ]
    )
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


def format_list(value: object) -> str:
    """Render a compact list for human-readable prompts."""
    if not isinstance(value, list) or not value:
        return "none"
    return ", ".join(str(item) for item in value)


def format_inline_code_list(value: object) -> str:
    """Render a list of strings as inline-code Markdown."""
    if not isinstance(value, list) or not value:
        return "none"
    return ", ".join(f"`{item}`" for item in value)


def format_severity_summary_dict(value: object) -> str:
    """Render a serialized severity summary."""
    if not isinstance(value, dict):
        return "none"
    return format_severity_summary({str(key): int(item) for key, item in value.items()})


def suggested_fix_order(
    failures: list[FailureContext], deep: DeepContext | None
) -> list[str]:
    """Return deterministic repair order including deep findings."""
    order = [failure.id for failure in failures]
    if has_blocking_deep_findings(deep) and "sg_scan" not in order:
        order.append("sg_scan")
    return order


def done_when_items(repair_needed: bool, deep: DeepContext | None) -> list[str]:
    """Return completion criteria with deep context when relevant."""
    if not repair_needed:
        return PASSING_DONE_WHEN
    items = list(DEFAULT_DONE_WHEN)
    if has_blocking_deep_findings(deep):
        items.append("qa-z deep exits with code 0")
        items.append("No blocking deep findings remain")
    return items


def has_blocking_deep_findings(deep: DeepContext | None) -> bool:
    """Return whether deep context contains blocking findings."""
    return bool(deep is not None and deep.blocking_findings_count > 0)


def blocking_grouped_findings(deep: dict[str, Any]) -> list[dict[str, Any]]:
    """Return grouped findings whose severities are configured as blocking."""
    grouped = deep.get("top_grouped_findings")
    if not isinstance(grouped, list):
        return []
    blocking = blocking_severities(deep)
    return [
        finding
        for finding in grouped
        if isinstance(finding, dict)
        and str(finding.get("severity", "")).upper() in blocking
    ]


def blocking_severities(deep: dict[str, Any]) -> set[str]:
    """Return blocking severities from deep policy metadata."""
    policy = deep.get("policy")
    if not isinstance(policy, dict):
        return {"ERROR"}
    severities = policy.get("fail_on_severity")
    if not isinstance(severities, list):
        return {"ERROR"}
    normalized = {str(item).upper() for item in severities if str(item).strip()}
    return normalized or {"ERROR"}


def format_grouped_finding(finding: dict[str, Any]) -> str:
    """Render one grouped finding in repair-prompt style."""
    count = int(finding.get("count") or 1)
    occurrence = "occurrence" if count == 1 else "occurrences"
    path = str(finding.get("path") or "unknown")
    line = finding.get("representative_line")
    location = f"{path}:{line}" if line else path
    return (
        "- "
        f"`{finding.get('rule_id', 'unknown')}` in `{location}` "
        f"({count} {occurrence}) - {finding.get('message', '')}"
    )


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
