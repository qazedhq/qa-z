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
    refresh_backlog_if_requested(root=root, refresh=args.refresh)
    backlog = load_backlog(root)
    if args.json:
        print(json.dumps(backlog, indent=2, sort_keys=True), end="\n")
    else:
        print(render_backlog(backlog, refreshed=args.refresh))
    return 0


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
