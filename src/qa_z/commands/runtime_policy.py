"""Policy pack CLI commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from qa_z.commands.common import resolve_cli_path
from qa_z.config import ConfigError, load_config
from qa_z.policy import resolve_policy_pack, validation_payload


def handle_policy_validate(args: argparse.Namespace) -> int:
    """Validate a local or builtin merge policy pack."""
    root = Path(args.path).expanduser().resolve()
    config_path = resolve_cli_path(root, args.config) if args.config else None
    try:
        config = load_config(root, config_path=config_path)
    except ConfigError as exc:
        payload: dict[str, Any] = {
            "kind": "qa_z.policy_validation",
            "schema_version": 1,
            "status": "invalid",
            "policy": {},
            "errors": [str(exc)],
        }
    else:
        policy = resolve_policy_pack(config, args.policy)
        payload = validation_payload(policy)

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=False))
    else:
        print(render_policy_validation_text(payload), end="")
    return 0 if payload["status"] == "valid" else 1


def render_policy_validation_text(payload: dict[str, Any]) -> str:
    """Render policy validation for terminal output."""
    policy = payload.get("policy")
    policy_name = policy.get("name") if isinstance(policy, dict) else "unknown"
    lines = [
        f"QA-Z policy validation: {payload.get('status')}",
        f"Policy: {policy_name}",
    ]
    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        lines.append("Errors:")
        lines.extend(f"- {error}" for error in errors)
    return "\n".join(lines).rstrip() + "\n"


def register_policy_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the policy command group."""
    policy_parser = subparsers.add_parser(
        "policy",
        help="validate local merge policy packs",
    )
    policy_subparsers = policy_parser.add_subparsers(dest="policy_command")
    validate_parser = policy_subparsers.add_parser(
        "validate",
        help="validate a builtin or configured merge policy",
    )
    validate_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml",
    )
    validate_parser.add_argument("--config", help="optional explicit config path")
    validate_parser.add_argument(
        "--policy",
        help="builtin or configured policy name, such as strict",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        help="print stable machine-readable JSON",
    )
    validate_parser.set_defaults(handler=handle_policy_validate)
