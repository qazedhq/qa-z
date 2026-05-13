"""Self-inspect planning CLI command handler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.commands.planning_output import render_self_inspect_stdout
from qa_z.self_improvement import run_self_inspection


def handle_self_inspect(args: argparse.Namespace) -> int:
    """Inspect local QA-Z artifacts and update the improvement backlog."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    try:
        paths = run_self_inspection(root=root)
        report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    except OSError as exc:
        return _self_inspect_error(
            args,
            error="artifact_write_error",
            message=(
                "qa-z self-inspect: artifact write error: "
                f"could not write self-inspection artifacts: {exc}"
            ),
        )
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True), end="\n")
    else:
        print(
            render_self_inspect_stdout(
                report,
                self_inspection_path=paths.self_inspection_path,
                backlog_path=paths.backlog_path,
                root=root,
            )
        )
    return 0


def _self_inspect_error(
    args: argparse.Namespace, *, error: str, message: str, exit_code: int = 2
) -> int:
    if args.json:
        print(
            json.dumps(
                {
                    "kind": "qa_z.self_inspect_error",
                    "error": error,
                    "exit_code": exit_code,
                    "message": message,
                },
                sort_keys=True,
            )
        )
    else:
        print(message)
    return exit_code


def register_self_inspect_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the self-inspect command."""
    self_inspect_parser = subparsers.add_parser(
        "self-inspect",
        help="inspect local QA-Z artifacts and update the improvement backlog",
    )
    self_inspect_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    self_inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable self-inspection report to stdout",
    )
    self_inspect_parser.set_defaults(handler=handle_self_inspect)
