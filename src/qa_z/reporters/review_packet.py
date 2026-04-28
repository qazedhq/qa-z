"""Render review packets from QA-Z contracts and run artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    ContractContext,
    RunSource,
    contract_output_dir as artifact_contract_output_dir,
    find_latest_contract as artifact_find_latest_contract,
    format_path,
    load_contract_context,
)
from qa_z.reporters.deep_context import build_deep_context
from qa_z.reporters.review_packet_contract import (
    contract_output_dir,
    find_latest_contract,
    load_contract_review_context,
)
from qa_z.reporters.review_packet_contract_markdown import (
    bulletize,
    extract_bullet_or_lines,
    extract_section,
    extract_subsection,
)
from qa_z.reporters.review_packet_render import (
    render_review_packet,
    render_run_review_packet,
    review_packet_json,
    run_review_packet_json,
    write_review_artifacts,
)
from qa_z.reporters.review_packet_sections import (
    check_summary,
    evidence_tail,
    failed_check_summary,
    format_affected_files,
    format_check_list,
    format_deep_check_run_sentence,
    format_grouped_finding,
    ordered_failed_checks,
    render_deep_findings_markdown,
    render_failed_check,
    render_selection_markdown,
)
from qa_z.runners.models import RunSummary

__all__ = [
    "bulletize",
    "check_summary",
    "contract_output_dir",
    "evidence_tail",
    "extract_bullet_or_lines",
    "extract_section",
    "extract_subsection",
    "failed_check_summary",
    "find_latest_contract",
    "format_affected_files",
    "format_check_list",
    "format_deep_check_run_sentence",
    "format_grouped_finding",
    "load_contract_review_context",
    "ordered_failed_checks",
    "render_deep_findings_markdown",
    "render_failed_check",
    "render_review_packet",
    "render_run_review_packet",
    "render_selection_markdown",
    "review_packet_json",
    "run_review_packet_json",
    "write_review_artifacts",
]


def _contract_output_dir_impl(root: Path, config: dict) -> Path:
    """Resolve the configured contract directory."""
    return artifact_contract_output_dir(root, config)


def _find_latest_contract_impl(root: Path, config: dict) -> Path:
    """Find the newest contract in the configured output directory."""
    return artifact_find_latest_contract(root, config)


def _render_review_packet_impl(contract_path: Path, root: Path) -> str:
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


def _review_packet_json_impl(contract_path: Path, root: Path) -> str:
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


def _render_run_review_packet_impl(
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
        _render_review_packet_impl(Path(root / (contract.path or "")), root).rstrip(),
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


def _run_review_packet_json_impl(
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


def _write_review_artifacts_impl(
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


def _load_contract_review_context_impl(
    contract_path: Path, root: Path
) -> ContractContext:
    """Load contract context for callers that need a shared parser."""
    return load_contract_context(contract_path, root)
