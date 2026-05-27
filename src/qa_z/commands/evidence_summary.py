"""CLI command for local QA-Z evidence summaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from qa_z.commands.common import load_cli_config, resolve_cli_path
from qa_z.evidence_summary import build_evidence_summary


def handle_summary(args: argparse.Namespace) -> int:
    """Render a local evidence navigator for a QA-Z run."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(
        root,
        args,
        "summary",
        json_error_kind="qa_z.evidence_summary_error",
    )
    if config is None:
        return 2

    payload = build_evidence_summary(
        root=root,
        config=config,
        from_run=args.from_run,
    )
    if args.json:
        rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    elif args.markdown:
        rendered = render_summary_markdown(payload)
    else:
        rendered = render_summary_text(payload)

    print(rendered, end="")
    if args.output:
        output_path = resolve_cli_path(root, args.output)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(
                f"qa-z summary: could not write --output {output_path}: {exc}",
                file=sys.stderr,
            )
            return 2
    return 0


def render_summary_text(payload: dict[str, Any]) -> str:
    """Render a short terminal-friendly evidence summary."""
    lines = [
        f"QA-Z Summary: {payload.get('status')}",
        f"Verdict: {payload.get('verdict')}",
    ]
    run_dir = payload.get("run_dir")
    lines.append(f"Run: {run_dir if run_dir else 'not found'}")
    lines.extend(["", "Evidence:"])
    evidence = payload.get("evidence")
    if isinstance(evidence, dict):
        for label, key in (
            ("fast summary", "fast_summary"),
            ("deep summary", "deep_summary"),
            ("repair prompt", "repair_prompt"),
            ("verify report", "verify_report"),
        ):
            entry = payload.get(key) if key in payload else evidence.get(key)
            if isinstance(entry, dict):
                lines.append(render_evidence_line(label, entry))

    top_findings = payload.get("top_findings")
    if isinstance(top_findings, list) and top_findings:
        lines.extend(["", "Top risks:"])
        for index, finding in enumerate(top_findings[:5], start=1):
            if isinstance(finding, dict):
                lines.append(f"{index}. {format_finding(finding)}")

    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "Warnings:"])
        for warning in warnings[:3]:
            lines.append(f"- {warning}")

    lines.extend(["", "Next actions:"])
    for index, action in enumerate(payload.get("next_actions", []), start=1):
        lines.append(f"{index}. Run `{action}`")
    return "\n".join(lines).rstrip() + "\n"


def render_summary_markdown(payload: dict[str, Any]) -> str:
    """Render the evidence summary as Markdown."""
    lines = [
        "# QA-Z Evidence Summary",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Verdict: `{payload.get('verdict')}`",
        f"- Run: `{payload.get('run_dir') or 'not found'}`",
        "",
        "## Evidence",
        "",
    ]
    evidence = payload.get("evidence")
    if isinstance(evidence, dict):
        for label, key in (
            ("Fast summary", "fast_summary"),
            ("Deep summary", "deep_summary"),
            ("Review packet", "review_packet"),
            ("GitHub summary", "github_summary"),
            ("Guard verdict", "guard_verdict"),
        ):
            entry = evidence.get(key)
            if isinstance(entry, dict):
                lines.append(f"- {label}: {format_entry_markdown(entry)}")
    repair_prompt = payload.get("repair_prompt")
    if isinstance(repair_prompt, dict):
        lines.append(f"- Repair prompt: {format_entry_markdown(repair_prompt)}")
    verify_report = payload.get("verify_report")
    if isinstance(verify_report, dict):
        lines.append(f"- Verify report: {format_entry_markdown(verify_report)}")

    top_findings = payload.get("top_findings")
    if isinstance(top_findings, list) and top_findings:
        lines.extend(["", "## Top Risks", ""])
        for finding in top_findings[:5]:
            if isinstance(finding, dict):
                lines.append(f"- {format_finding(finding)}")

    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    lines.extend(["", "## Next Actions", ""])
    lines.extend(
        f"{index}. `{action}`"
        for index, action in enumerate(payload.get("next_actions", []), start=1)
    )
    return "\n".join(lines).rstrip() + "\n"


def render_evidence_line(label: str, entry: dict[str, Any]) -> str:
    """Render one human evidence line."""
    marker = "PASS" if entry.get("exists") else "MISS"
    status = entry.get("status")
    path = entry.get("path") or "not found"
    if status:
        return f"{marker} {label}: {status} ({path})"
    return f"{marker} {label}: {path}"


def format_entry_markdown(entry: dict[str, Any]) -> str:
    """Render one Markdown evidence entry."""
    path = entry.get("path") or "not found"
    exists = "found" if entry.get("exists") else "missing"
    status = entry.get("status")
    suffix = f", `{status}`" if status else ""
    return f"`{path}` ({exists}{suffix})"


def format_finding(finding: dict[str, Any]) -> str:
    """Render one top risk finding."""
    source = finding.get("source") or "evidence"
    finding_id = finding.get("id") or "finding"
    message = finding.get("message") or "No message"
    path = finding.get("path")
    line = finding.get("line")
    location = ""
    if path and line:
        location = f" at {path}:{line}"
    elif path:
        location = f" at {path}"
    return f"{source}:{finding_id}{location} - {message}"


def register_summary_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the local evidence summary command."""
    summary_parser = subparsers.add_parser(
        "summary",
        help="summarize verdicts, risks, evidence paths, and next commands",
    )
    summary_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    summary_parser.add_argument("--config", help="optional explicit config path")
    summary_parser.add_argument(
        "--from-run",
        default="latest",
        help="run root, fast directory, summary.json, or latest",
    )
    summary_parser.add_argument(
        "--json",
        action="store_true",
        help="print stable machine-readable JSON",
    )
    summary_parser.add_argument(
        "--markdown",
        action="store_true",
        help="print a Markdown evidence summary",
    )
    summary_parser.add_argument(
        "--output",
        help="optional path to write the rendered summary",
    )
    summary_parser.set_defaults(handler=handle_summary)
