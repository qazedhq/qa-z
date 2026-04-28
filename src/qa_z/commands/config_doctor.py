"""qa-z doctor CLI command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.commands.common import resolve_cli_path
from qa_z.config import ConfigError, load_config
from qa_z.config_validation import validate_config


def handle_doctor(args: argparse.Namespace) -> int:
    """Validate local QA-Z configuration."""
    root = Path(args.path).expanduser().resolve()
    config_path = resolve_cli_path(root, args.config) if args.config else None
    try:
        config = load_config(root, config_path=config_path)
        report = validate_config(root, config)
    except ConfigError as exc:
        report = {
            "status": "failed",
            "errors": [
                {
                    "code": "config_error",
                    "path": str(config_path or root / "qa-z.yaml"),
                    "message": str(exc),
                }
            ],
            "warnings": [],
            "suggestions": [],
        }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"qa-z doctor: {report['status']}")
        for item in report["errors"]:
            print(f"error {item['code']} at {item['path']}: {item['message']}")
        for item in report["warnings"]:
            print(f"warning {item['code']} at {item['path']}: {item['message']}")
        for suggestion in report["suggestions"]:
            print(f"suggestion: {suggestion}")

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
