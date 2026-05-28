"""CLI command for the one-command QA-Z guard workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.commands.common import resolve_cli_path
from qa_z.config import ConfigError, load_config
from qa_z.guard.renderer import render_guard_stdout
from qa_z.adapters import SUPPORTED_REPAIR_ADAPTERS
from qa_z.guard.workflow import run_guard
from qa_z.policy import resolve_policy_pack, validate_policy_pack


def handle_guard(args: argparse.Namespace) -> int:
    """Run the guard workflow and print a verdict."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config_path = resolve_cli_path(root, args.config) if args.config else None
    try:
        config = load_config(root, config_path=config_path)
    except ConfigError as exc:
        return _guard_error(
            args,
            error="configuration_error",
            message=f"qa-z guard: configuration error: {exc}",
        )
    policy = None
    if args.policy:
        policy = resolve_policy_pack(config, args.policy)
        policy_errors = validate_policy_pack(policy)
        if policy_errors:
            return _guard_error(
                args,
                error="policy_error",
                message="qa-z guard: policy error: " + "; ".join(policy_errors),
            )
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
            policy=policy,
        )
    except (FileNotFoundError, ValueError) as exc:
        return _guard_error(
            args,
            error="guard_error",
            message=f"qa-z guard: error: {exc}",
        )
    except OSError as exc:
        return _guard_error(
            args,
            error="artifact_write_error",
            message=f"qa-z guard: artifact error: {exc}",
        )

    if args.json:
        print(json.dumps(verdict.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_guard_stdout(verdict), end="")

    if args.fail_on_risk and verdict.status in {"do_not_merge", "error"}:
        return 1
    return 0


def _guard_error(
    args: argparse.Namespace, *, error: str, message: str, exit_code: int = 2
) -> int:
    if args.json:
        print(
            json.dumps(
                {
                    "kind": "qa_z.guard_error",
                    "error": error,
                    "exit_code": exit_code,
                    "message": message,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(message)
    return exit_code


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
        choices=SUPPORTED_REPAIR_ADAPTERS,
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
    guard_parser.add_argument(
        "--policy",
        help="optional builtin or configured merge policy, such as strict",
    )
    guard_parser.set_defaults(handler=handle_guard)
