"""Select-next planning CLI command handler."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.commands.planning_output import render_select_next_stdout
from qa_z.commands.planning_refresh import refresh_backlog_if_requested
from qa_z.self_improvement import select_next_tasks


def handle_select_next(args: argparse.Namespace) -> int:
    """Select the next highest-priority self-improvement tasks."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    refresh_backlog_if_requested(root=root, refresh=args.refresh)
    paths = select_next_tasks(root=root, count=args.count)
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(selected, indent=2, sort_keys=True), end="\n")
    else:
        print(render_select_next_stdout(selected, paths, root, refreshed=args.refresh))
    return 0


def register_select_next_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the select-next command."""
    select_next_parser = subparsers.add_parser(
        "select-next",
        help="select the next 1 to 3 self-improvement backlog tasks",
    )
    select_next_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains the improvement backlog",
    )
    select_next_parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="number of open tasks to select, clamped to 1 through 3",
    )
    select_next_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable selected-tasks artifact to stdout",
    )
    select_next_parser.add_argument(
        "--refresh",
        action="store_true",
        help="run self-inspection before selecting backlog tasks",
    )
    select_next_parser.set_defaults(handler=handle_select_next)
