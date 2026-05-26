"""qa-z doctor CLI command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.commands.common import resolve_cli_path
from qa_z.doctor import build_doctor_report, render_doctor_human


def handle_doctor(args: argparse.Namespace) -> int:
    """Validate local QA-Z configuration."""
    root = Path(args.path).expanduser().resolve()
    config_path = resolve_cli_path(root, args.config) if args.config else None
    report = build_doctor_report(root, config_path=config_path)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_doctor_human(report))

    if report["errors"]:
        return 1
    if args.strict and report["warnings"]:
        return 1
    return 0


def register_doctor_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the doctor command."""
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="validate QA-Z config and local onboarding files",
    )
    doctor_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml",
    )
    doctor_parser.add_argument(
        "--config",
        help="optional config path, relative to --path unless absolute",
    )
    doctor_parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable validation output",
    )
    doctor_parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero when warnings are present",
    )
    doctor_parser.set_defaults(handler=handle_doctor)
