"""CLI command for the one-command QA-Z guard workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.commands.common import load_cli_config
from qa_z.guard.renderer import render_guard_stdout
from qa_z.guard.workflow import run_guard


def handle_guard(args: argparse.Namespace) -> int:
    """Run the guard workflow and print a verdict."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "guard")
    if config is None:
        return 2
    try:
        verdict = run_guard(
            root=root,
            config=config,
            title=args.title,
            slug=args.slug,
            adapter=args.adapter,
            deep_mode=args.deep,
            github_summary=args.github_summary,
            from_run=args.from_run,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"qa-z guard: error: {exc}")
        return 2

    if args.json:
        print(json.dumps(verdict.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_guard_stdout(verdict), end="")

    if args.fail_on_risk and verdict.status in {"do_not_merge", "error"}:
        return 1
    return 0


def register_guard_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the guard command."""
    guard_parser = subparsers.add_parser(
        "guard",
        help="run the one-command QA-Z merge guard",
    )
    guard_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml",
    )
    guard_parser.add_argument("--config", help="optional explicit config path")
    guard_parser.add_argument("--title", help="optional contract title")
    guard_parser.add_argument("--slug", help="optional contract slug")
    guard_parser.add_argument(
        "--adapter",
        choices=("codex", "claude", "human"),
        default="codex",
        help="repair-prompt audience metadata",
    )
    guard_parser.add_argument(
        "--deep",
        choices=("auto", "always", "never"),
        default="auto",
        help="deep-check policy for the guard",
    )
    guard_parser.add_argument(
        "--github-summary",
        action="store_true",
        help="write a GitHub summary artifact under the guard directory",
    )
    guard_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable guard verdict",
    )
    guard_parser.add_argument(
        "--fail-on-risk",
        action="store_true",
        help="exit nonzero for do_not_merge or error verdicts",
    )
    guard_parser.add_argument(
        "--from-run",
        help="optional run root, fast directory, summary.json, or latest fast run artifact",
    )
    guard_parser.set_defaults(handler=handle_guard)
