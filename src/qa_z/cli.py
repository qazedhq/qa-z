"""Command line interface for QA-Z."""

from __future__ import annotations

import argparse
from typing import Iterable

from .commands import register_modular_commands
from .commands.planning_output import (
    render_backlog,
    render_select_next_stdout,
    render_self_inspect_stdout,
)

__all__ = [
    "build_parser",
    "main",
    "render_backlog",
    "render_select_next_stdout",
    "render_self_inspect_stdout",
]


def build_parser() -> argparse.ArgumentParser:
    """Build the root CLI parser."""
    parser = argparse.ArgumentParser(
        prog="qa-z",
        description="QA-Z is a QA control plane scaffold for coding agents.",
    )
    subparsers = parser.add_subparsers(dest="command")
    register_modular_commands(subparsers)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    return int(args.handler(args))
