"""Executor bridge CLI commands for local runtime workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound
from qa_z.commands.common import resolve_cli_path
from qa_z.executor_bridge import (
    ExecutorBridgeError,
    create_executor_bridge,
    render_bridge_stdout,
)

__all__ = [
    "handle_executor_bridge",
    "register_executor_bridge_command",
]


def handle_executor_bridge(args: argparse.Namespace) -> int:
    """Package autonomy/session evidence for an external executor."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if bool(args.from_loop) == bool(args.from_session):
        print(
            "qa-z executor-bridge: configuration error: provide exactly one of "
            "--from-loop or --from-session."
        )
        return 2
    output_dir = resolve_cli_path(root, args.output_dir) if args.output_dir else None
    try:
        paths = create_executor_bridge(
            root=root,
            from_loop=args.from_loop,
            from_session=args.from_session,
            bridge_id=args.bridge_id,
            output_dir=output_dir,
        )
        manifest = json.loads(paths.manifest_path.read_text(encoding="utf-8"))
        if args.json:
            print(json.dumps(manifest, indent=2, sort_keys=True), end="\n")
        else:
            print(render_bridge_stdout(manifest))
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z executor-bridge: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z executor-bridge: source not found: {exc}")
        return 4
    except ExecutorBridgeError as exc:
        print(f"qa-z executor-bridge: configuration error: {exc}")
        return 2


def register_executor_bridge_command(
    subparsers: argparse._SubParsersAction,
) -> None:
    """Register the executor-bridge command."""
    executor_bridge_parser = subparsers.add_parser(
        "executor-bridge",
        help="package a repair session for an external executor",
    )
    executor_bridge_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    bridge_source_group = executor_bridge_parser.add_mutually_exclusive_group(
        required=True
    )
    bridge_source_group.add_argument(
        "--from-loop",
        help="autonomy loop id, loop directory, or outcome.json path",
    )
    bridge_source_group.add_argument(
        "--from-session",
        help="repair-session id, session directory, or session.json path",
    )
    executor_bridge_parser.add_argument(
        "--bridge-id",
        help="optional stable bridge id; defaults to timestamp plus source id",
    )
    executor_bridge_parser.add_argument(
        "--output-dir",
        help="optional bridge package directory; defaults to .qa-z/executor/<bridge-id>",
    )
    executor_bridge_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable bridge manifest to stdout",
    )
    executor_bridge_parser.set_defaults(handler=handle_executor_bridge)
