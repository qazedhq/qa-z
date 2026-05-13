"""Backlog planning CLI command handler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.commands.planning_output import render_backlog
from qa_z.commands.planning_refresh import refresh_backlog_if_requested
from qa_z.improvement_state import load_backlog


def handle_backlog(args: argparse.Namespace) -> int:
    """Print the current improvement backlog."""
    root = Path(args.path).expanduser().resolve()
    try:
        refresh_backlog_if_requested(root=root, refresh=args.refresh)
        backlog = load_backlog(root)
    except OSError as exc:
        return _backlog_error(
            args,
            error="artifact_write_error",
            message=(
                "qa-z backlog: artifact write error: "
                f"could not refresh backlog artifacts: {exc}"
            ),
        )
    if args.json:
        print(json.dumps(backlog, indent=2, sort_keys=True), end="\n")
    else:
        print(render_backlog(backlog, refreshed=args.refresh))
    return 0


def _backlog_error(
    args: argparse.Namespace, *, error: str, message: str, exit_code: int = 2
) -> int:
    if args.json:
        print(
            json.dumps(
                {
                    "kind": "qa_z.backlog_error",
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


def register_backlog_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the backlog command."""
    backlog_parser = subparsers.add_parser(
        "backlog",
        help="print the current QA-Z improvement backlog",
    )
    backlog_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains the improvement backlog",
    )
    backlog_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable improvement backlog to stdout",
    )
    backlog_parser.add_argument(
        "--refresh",
        action="store_true",
        help="run self-inspection before printing the backlog",
    )
    backlog_parser.set_defaults(handler=handle_backlog)
