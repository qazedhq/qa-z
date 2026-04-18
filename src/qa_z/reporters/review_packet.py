"""Render review packets from QA-Z contracts and run artifacts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    ContractContext,
    RunSource,
    contract_output_dir as artifact_contract_output_dir,
    extract_candidate_files,
    find_latest_contract as artifact_find_latest_contract,
    format_path,
    load_contract_context,
)
from qa_z.reporters.deep_context import (
    DeepContext,
    build_deep_context,
    format_finding_location,
    format_severity_summary,
)
from qa_z.reporters.repair_prompt import fix_priority
from qa_z.runners.models import CheckResult, RunSummary


def contract_output_dir(root: Path, config: dict) -> Path:
    """Resolve the configured contract directory."""
    return artifact_contract_output_dir(root, config)


def find_latest_contract(root: Path, config: dict) -> Path:
    """Find the newest contract in the configured output directory."""
    return artifact_find_latest_contract(root, config)


def extract_section(document: str, heading: str) -> str:
    """Extract a markdown section body by H2 heading."""
    pattern = rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, document, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return match.group("body").strip()


def extract_subsection(document: str, heading: str) -> str:
    """Extract a markdown subsection body by H3 heading."""
    pattern = rf"^### {re.escape(heading)}\n(?P<body>.*?)(?=^### |^## |\Z)"
    match = re.search(pattern, document, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return match.group("body").strip()


def bulletize(text: str, fallback: str) -> str:
    """Normalize text blocks into bullet lists."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return f"- {fallback}"
    bullets = [line if line.startswith("- ") else f"- {line}" for line in lines]
    return "\n".join(bullets)


def render_review_packet(contract_path: Path, root: Path) -> str:
    """Render a review packet from a generated contract."""
    document = contract_path.read_text(encoding="utf-8")
    relative_contract = format_path(contract_path, root)
    risk_edges = extract_section(document, "Risk Edges")
    negative_cases = extract_section(document, "Negative Cases")
    acceptance_checks = extract_section(document, "Acceptance Checks")
    fast_checks = extract_subsection(document, "Fast")
    deep_checks = extract_subsection(document, "Deep")

    lines = [
        "# QA-Z Review Packet",
        "",
        f"- Contract: {relative_contract}",
        "- Mode: qa-z review",
        "",
        "## Reviewer Focus",
        "",
        bulletize(risk_edges, "No explicit risk edges found."),
        "",
        "## Negative Cases To Check",
        "",
        bulletize(negative_cases, "No negative cases listed."),
        "",
        "## Required Evidence",
        "",
        bulletize(acceptance_checks, "No acceptance checks listed."),
        "",
        "## Suggested Fast Checks",
        "",
        bulletize(fast_checks, "No fast checks configured."),
        "",
        "## Suggested Deep Checks",
        "",
        bulletize(deep_checks, "No deep checks configured."),
    ]
    return "\n".join(lines).strip() + "\n"


def review_packet_json(contract_path: Path, root: Path) -> str:
    """Render the contract-only review packet as JSON."""
    document = contract_path.read_text(encoding="utf-8")
    packet = {
        "version": 1,
        "contract": {
            "path": format_path(contract_path, root),
            "risk_edges": extract_bullet_or_lines(
                extract_section(document, "Risk Edges")
            ),
            "negative_cases": extract_bullet_or_lines(
                extract_section(document, "Negative Cases")
            ),
            "acceptance_checks": extract_bullet_or_lines(
                extract_section(document, "Acceptance Checks")
            ),
            "fast_checks": extract_bullet_or_lines(
                extract_subsection(document, "Fast")
            ),
            "deep_checks": extract_bullet_or_lines(
                extract_subsection(document, "Deep")
            ),
        },
    }
    return json.dumps(packet, indent=2, sort_keys=True) + "\n"


def render_run_review_packet(
    *,
    summary: RunSummary,
    run_source: RunSource,
    contract: ContractContext,
    root: Path,
    deep_summary: RunSummary | None = None,
) -> str:
    """Render a review packet enriched with fast run context."""
    deep_context = build_deep_context(deep_summary)
    lines = [
        render_review_packet(Path(root / (contract.path or "")), root).rstrip(),
        "",
        "## Run Verdict",
        "",
        f"- Status: {summary.status}",
        f"- Run directory: `{format_path(run_source.run_dir, root)}`",
        f"- Summary: `{format_path(run_source.summary_path, root)}`",
        "",
    ]
    lines.extend(render_selection_markdown(summary))
    lines.extend(["## Executed Checks", ""])
    if not summary.checks:
        lines.append("- No checks were executed.")
    else:
        for check in summary.checks:
            lines.append(
                f"- {check.id}: {check.status} ({check.kind}, {check.tool}, exit {check.exit_code})"
            )
    lines.extend(["", "## Failed Checks", ""])

    failed_checks = ordered_failed_checks(summary)
    if not failed_checks:
        lines.extend(["No failed checks were found.", ""])
    for check in failed_checks:
        lines.extend(render_failed_check(check))

    lines.extend(["## Review Priority Order", ""])
    if not failed_checks:
        lines.append("No failed checks require priority ordering.")
    else:
        for index, check in enumerate(failed_checks, start=1):
            lines.append(f"{index}. {check.id}")
    lines.extend(render_deep_findings_markdown(deep_context))
    return "\n".join(lines).strip() + "\n"


def run_review_packet_json(
    *,
    summary: RunSummary,
    run_source: RunSource,
    contract: ContractContext,
    root: Path,
    deep_summary: RunSummary | None = None,
) -> str:
    """Render run-aware review context as JSON."""
    failed_checks = ordered_failed_checks(summary)
    deep_context = build_deep_context(deep_summary)
    packet: dict[str, Any] = {
        "version": 1,
        "contract": {
            "path": contract.path,
            "title": contract.title,
            "summary": contract.summary,
            "scope_items": contract.scope_items,
            "acceptance_checks": contract.acceptance_checks,
        },
        "run": {
            "dir": format_path(run_source.run_dir, root),
            "summary_path": format_path(run_source.summary_path, root),
            "status": summary.status,
            "started_at": summary.started_at,
            "finished_at": summary.finished_at,
            "selection": (
                summary.selection.to_dict() if summary.selection is not None else None
            ),
        },
        "executed_checks": [check_summary(check) for check in summary.checks],
        "failed_checks": [failed_check_summary(check) for check in failed_checks],
        "review_priority_order": [check.id for check in failed_checks],
        "deep": deep_context.to_dict() if deep_context else None,
    }
    return json.dumps(packet, indent=2, sort_keys=True) + "\n"


def write_review_artifacts(
    markdown: str, json_text: str | None, output_dir: Path
) -> tuple[Path, Path | None]:
    """Write review Markdown and optional JSON artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / "review.md"
    markdown_path.write_text(markdown, encoding="utf-8")
    json_path = None
    if json_text is not None:
        json_path = output_dir / "review.json"
        json_path.write_text(json_text, encoding="utf-8")
    return markdown_path, json_path


def load_contract_review_context(contract_path: Path, root: Path) -> ContractContext:
    """Load contract context for callers that need a shared parser."""
    return load_contract_context(contract_path, root)


def ordered_failed_checks(summary: RunSummary) -> list[CheckResult]:
    """Return failed or errored checks in review priority order."""
    failed = [check for check in summary.checks if check.status in {"failed", "error"}]
    return [
        check
        for _index, check in sorted(
            enumerate(failed), key=lambda item: (fix_priority(item[1]), item[0])
        )
    ]


def render_failed_check(check: CheckResult) -> list[str]:
    """Render one failed check with evidence tail."""
    lines = [
        f"### {check.id}",
        "",
        f"- Tool: {check.tool}",
        f"- Kind: {check.kind}",
        f"- Command: `{' '.join(check.command)}`",
        f"- Exit code: `{check.exit_code}`",
    ]
    candidates = extract_candidate_files(
        "\n".join(part for part in (check.stdout_tail, check.stderr_tail) if part)
    )
    if candidates:
        lines.append("- Candidate files:")
        lines.extend(f"  - `{path}`" for path in candidates)
    lines.extend(["", "Evidence:", "```text", evidence_tail(check), "```", ""])
    return lines


def check_summary(check: CheckResult) -> dict[str, Any]:
    """Render compact check metadata for review JSON."""
    return {
        "id": check.id,
        "kind": check.kind,
        "tool": check.tool,
        "command": check.command,
        "status": check.status,
        "exit_code": check.exit_code,
        "duration_ms": check.duration_ms,
        "execution_mode": check.execution_mode,
        "target_paths": check.target_paths,
        "selection_reason": check.selection_reason,
        "high_risk_reasons": check.high_risk_reasons,
    }


def failed_check_summary(check: CheckResult) -> dict[str, Any]:
    """Render failed check metadata with evidence for review JSON."""
    data = check_summary(check)
    data["stdout_tail"] = check.stdout_tail
    data["stderr_tail"] = check.stderr_tail
    data["candidate_files"] = extract_candidate_files(
        "\n".join(part for part in (check.stdout_tail, check.stderr_tail) if part)
    )
    return data


def extract_bullet_or_lines(section: str) -> list[str]:
    """Normalize a markdown section into a JSON list."""
    items = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ")):
            stripped = stripped[2:].strip()
        items.append(stripped)
    return items


def evidence_tail(check: CheckResult) -> str:
    """Combine stdout and stderr tails for display."""
    parts = []
    if check.stdout_tail:
        parts.append(check.stdout_tail.rstrip())
    if check.stderr_tail:
        parts.append(check.stderr_tail.rstrip())
    return "\n".join(parts) if parts else "No stdout or stderr tail captured."


def render_selection_markdown(summary: RunSummary) -> list[str]:
    """Render v2 check-selection context when present."""
    if summary.selection is None:
        return []
    selection = summary.selection
    return [
        "## Check Selection",
        "",
        f"- Mode: {selection.mode}",
        f"- Input source: {selection.input_source}",
        f"- Changed files: {len(selection.changed_files)}",
        f"- Full checks: {format_check_list(selection.full_checks)}",
        f"- Targeted checks: {format_check_list(selection.targeted_checks)}",
        f"- Skipped checks: {format_check_list(selection.skipped_checks)}",
        f"- High-risk reasons: {format_check_list(selection.high_risk_reasons)}",
        "",
    ]


def format_check_list(items: list[str]) -> str:
    """Render a compact comma-separated list for review output."""
    return ", ".join(items) if items else "none"


def render_deep_findings_markdown(deep: DeepContext | None) -> list[str]:
    """Render optional deep findings for run-aware review packets."""
    if deep is None:
        return []
    lines = [
        "",
        "## Deep Findings",
        "",
        f"- Status: {deep.summary.status}",
        f"- Findings: {deep.findings_count}",
        f"- Blocking findings: {deep.blocking_findings_count}",
        f"- Filtered findings: {deep.filtered_findings_count}",
        f"- Highest severity: {deep.highest_severity or 'none'}",
        f"- Severity summary: {format_severity_summary(deep.severity_summary)}",
        f"- Affected files: {format_affected_files(deep.affected_files)}",
    ]
    if deep.primary_check is not None:
        lines.append(f"- {format_deep_check_run_sentence(deep)}")
        if deep.primary_check.selection_reason:
            lines.append(f"- Selection reason: {deep.primary_check.selection_reason}")

    if deep.grouped_findings:
        lines.extend(["", "Top grouped findings:"])
        for finding in deep.grouped_findings[:5]:
            lines.append(format_grouped_finding(finding))
    elif deep.findings:
        lines.extend(["", "Top findings:"])
        for finding in deep.findings[:5]:
            lines.append(
                "- "
                f"`{format_finding_location(finding)}` "
                f"{finding['severity']} {finding['rule_id']} - {finding['message']}"
            )
    else:
        lines.extend(["", "No Semgrep findings were reported."])
    return lines


def format_deep_check_run_sentence(deep: DeepContext) -> str:
    """Render the primary deep check execution mode in one sentence."""
    check_id = deep.primary_check.id if deep.primary_check else "deep check"
    mode = deep.execution_mode
    if deep.target_count:
        noun = "file" if deep.target_count == 1 else "files"
        return f"`{check_id}` ran in {mode} mode for {deep.target_count} {noun}"
    return f"`{check_id}` ran in {mode} mode"


def format_affected_files(paths: list[str]) -> str:
    """Render affected files for Markdown."""
    if not paths:
        return "none"
    return ", ".join(f"`{path}`" for path in paths)


def format_grouped_finding(finding: dict[str, Any]) -> str:
    """Render one grouped Semgrep finding for review packets."""
    count = int(finding.get("count") or 1)
    occurrence = "occurrence" if count == 1 else "occurrences"
    location = format_finding_location(finding)
    return (
        "- "
        f"`{finding.get('rule_id', 'unknown')}` in `{location}` "
        f"({count} {occurrence}) - {finding.get('message', '')}"
    )
