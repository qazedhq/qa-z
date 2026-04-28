"""Plan bootstrap CLI command handler."""

from __future__ import annotations

import argparse
from pathlib import Path

from qa_z.commands.common import format_relative_path, load_cli_config, resolve_cli_path
from qa_z.planner.contracts import plan_contract


def handle_plan(args: argparse.Namespace) -> int:
    """Generate a QA contract draft from local context files."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "plan")
    if config is None:
        return 2

    contract_path, created = plan_contract(
        root=root,
        config=config,
        title=args.title,
        slug=args.slug,
        issue_path=resolve_cli_path(root, args.issue) if args.issue else None,
        spec_path=resolve_cli_path(root, args.spec) if args.spec else None,
        diff_path=resolve_cli_path(root, args.diff) if args.diff else None,
        overwrite=args.overwrite,
    )

    relative_contract_path = format_relative_path(contract_path, root)
    status = "created contract" if created else "kept existing contract"
    print(f"{status}: {relative_contract_path}")
    return 0


def register_plan_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the plan command."""
    plan_parser = subparsers.add_parser(
        "plan",
        help="generate a QA contract draft from title and context files",
    )
    plan_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and contract output directories",
    )
    plan_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    plan_parser.add_argument(
        "--title",
        help="human-readable title for the contract",
    )
    plan_parser.add_argument(
        "--slug",
        help="optional custom file slug for the generated contract",
    )
    plan_parser.add_argument(
        "--issue",
        help="optional path to issue context markdown or text",
    )
    plan_parser.add_argument(
        "--spec",
        help="optional path to spec context markdown or text",
    )
    plan_parser.add_argument(
        "--diff",
        help="optional path to a diff excerpt or patch file",
    )
    plan_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite an existing contract draft with the same slug",
    )
    plan_parser.set_defaults(handler=handle_plan)
