"""Team governance CLI commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from qa_z.governance import add_waiver, build_governance_report, create_baseline


def handle_baseline_create(args: argparse.Namespace) -> int:
    """Create a local governance baseline."""
    root = Path(args.path).expanduser().resolve()
    payload = create_baseline(root)
    print_payload(payload, args.json)
    return 0


def handle_waiver_add(args: argparse.Namespace) -> int:
    """Add a local governance waiver."""
    root = Path(args.path).expanduser().resolve()
    try:
        payload = add_waiver(
            root=root,
            finding_id=args.finding_id,
            owner=args.owner,
            reason=args.reason,
            expires=args.expires,
        )
    except ValueError as exc:
        payload = {
            "kind": "qa_z.governance_waiver_error",
            "schema_version": 1,
            "status": "invalid",
            "error": str(exc),
        }
        print_payload(payload, args.json)
        return 1
    print_payload(payload, args.json)
    return 0


def handle_governance_report(args: argparse.Namespace) -> int:
    """Render the local governance report."""
    root = Path(args.path).expanduser().resolve()
    payload = build_governance_report(root)
    print_payload(payload, args.json)
    return 0


def print_payload(payload: dict[str, Any], as_json: bool) -> None:
    """Print a governance payload."""
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=False))
        return
    print(render_governance_text(payload), end="")


def render_governance_text(payload: dict[str, Any]) -> str:
    """Render a compact governance payload."""
    kind = str(payload.get("kind") or "qa_z.governance")
    status = str(payload.get("status") or "unknown")
    lines = [f"{kind}: {status}"]
    waiver_summary = payload.get("waiver_summary")
    if isinstance(waiver_summary, dict):
        lines.append(f"Active waivers: {waiver_summary.get('active', 0)}")
        lines.append(f"Expired waivers: {waiver_summary.get('expired', 0)}")
    audit_trail = payload.get("audit_trail")
    if isinstance(audit_trail, list) and audit_trail:
        lines.append("Audit trail:")
        lines.extend(f"- {path}" for path in audit_trail)
    return "\n".join(lines).rstrip() + "\n"


def register_baseline_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the baseline command group."""
    baseline_parser = subparsers.add_parser(
        "baseline",
        help="create local governance baselines",
    )
    baseline_subparsers = baseline_parser.add_subparsers(dest="baseline_command")
    create_parser = baseline_subparsers.add_parser(
        "create",
        help="write a local governance baseline artifact",
    )
    create_parser.add_argument(
        "--path",
        default=".",
        help="repository root for the governance baseline",
    )
    create_parser.add_argument(
        "--json",
        action="store_true",
        help="print stable machine-readable JSON",
    )
    create_parser.set_defaults(handler=handle_baseline_create)


def register_waiver_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the waiver command group."""
    waiver_parser = subparsers.add_parser(
        "waiver",
        help="record local governance waivers",
    )
    waiver_subparsers = waiver_parser.add_subparsers(dest="waiver_command")
    add_parser = waiver_subparsers.add_parser(
        "add",
        help="append a local governance waiver",
    )
    add_parser.add_argument("--path", default=".", help="repository root")
    add_parser.add_argument("--finding-id", required=True, help="finding identifier")
    add_parser.add_argument("--owner", required=True, help="waiver owner")
    add_parser.add_argument("--reason", required=True, help="waiver reason")
    add_parser.add_argument(
        "--expires",
        required=True,
        help="waiver expiration date in YYYY-MM-DD format",
    )
    add_parser.add_argument(
        "--json",
        action="store_true",
        help="print stable machine-readable JSON",
    )
    add_parser.set_defaults(handler=handle_waiver_add)


def register_governance_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the governance command group."""
    governance_parser = subparsers.add_parser(
        "governance",
        help="render local governance reports",
    )
    governance_subparsers = governance_parser.add_subparsers(dest="governance_command")
    report_parser = governance_subparsers.add_parser(
        "report",
        help="summarize baseline and waiver artifacts",
    )
    report_parser.add_argument("--path", default=".", help="repository root")
    report_parser.add_argument(
        "--json",
        action="store_true",
        help="print stable machine-readable JSON",
    )
    report_parser.set_defaults(handler=handle_governance_report)
