"""Autonomy CLI commands for local deterministic runtime workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.autonomy import (
    load_autonomy_status,
    render_autonomy_status,
    render_autonomy_summary,
    run_autonomy,
)
from qa_z.commands.common import load_cli_config

__all__ = [
    "handle_autonomy",
    "register_autonomy_command",
]


def handle_autonomy(args: argparse.Namespace) -> int:
    """Run or inspect deterministic autonomy planning loops."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.autonomy_command == "status":
        status = load_autonomy_status(root)
        if args.json:
            print(json.dumps(status, indent=2, sort_keys=True), end="\n")
        else:
            print(render_autonomy_status(status))
        return 0

    config = load_cli_config(root, args, "autonomy")
    if config is None:
        return 2
    summary = run_autonomy(
        root=root,
        config=config,
        loops=args.loops,
        count=args.count,
        min_runtime_seconds=args.min_runtime_hours * 3600,
        min_loop_seconds=args.min_loop_seconds,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True), end="\n")
    else:
        print(render_autonomy_summary(summary, root))
    return 0


def register_autonomy_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the autonomy command."""
    autonomy_parser = subparsers.add_parser(
        "autonomy",
        help="run deterministic self-improvement planning loops",
    )
    autonomy_parser.add_argument(
        "autonomy_command",
        nargs="?",
        choices=("status",),
        help="print the latest autonomy workflow status",
    )
    autonomy_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    autonomy_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    autonomy_parser.add_argument(
        "--loops",
        type=int,
        default=1,
        help="number of planning loops to run",
    )
    autonomy_parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="number of open tasks to select per loop, clamped to 1 through 3",
    )
    autonomy_parser.add_argument(
        "--min-runtime-hours",
        type=float,
        default=0.0,
        help="minimum wall-clock runtime budget in hours before the run may finish",
    )
    autonomy_parser.add_argument(
        "--min-loop-seconds",
        type=float,
        default=0.0,
        help="minimum wall-clock duration to spend in each loop before advancing",
    )
    autonomy_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable autonomy summary or status",
    )
    autonomy_parser.set_defaults(handler=handle_autonomy)
