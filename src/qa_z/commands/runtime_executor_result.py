"""Executor-result CLI commands and dry-run rendering helpers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound
from qa_z.commands.common import load_cli_config, resolve_cli_path
from qa_z.commands.runtime_executor_result_stdout import (
    dry_run_action_summaries,
    dry_run_rule_counts,
    dry_run_text_field,
    render_executor_result_dry_run_stdout,
)
from qa_z.executor_dry_run import run_executor_result_dry_run
from qa_z.executor_ingest import (
    ExecutorResultIngestRejected,
    ingest_executor_result_artifact,
    render_executor_result_ingest_stdout,
)
from qa_z.verification import verify_exit_code

__all__ = [
    "dry_run_action_summaries",
    "dry_run_rule_counts",
    "dry_run_text_field",
    "handle_executor_result_dry_run",
    "handle_executor_result_ingest",
    "register_executor_result_command",
    "render_executor_result_dry_run_stdout",
]


def handle_executor_result_ingest(args: argparse.Namespace) -> int:
    """Ingest an external executor result and optionally resume verification."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "executor-result ingest")
    if config is None:
        return 2

    try:
        outcome = ingest_executor_result_artifact(
            root=root,
            config=config,
            result_path=resolve_cli_path(root, args.result),
        )
        if args.json:
            print(json.dumps(outcome.summary, indent=2, sort_keys=True), end="\n")
        else:
            print(render_executor_result_ingest_stdout(outcome.summary))
        if (
            outcome.summary.get("verification_triggered")
            and outcome.verification_verdict
        ):
            return verify_exit_code(outcome.verification_verdict)
        return 0
    except ExecutorResultIngestRejected as exc:
        if args.json:
            print(json.dumps(exc.outcome.summary, indent=2, sort_keys=True), end="\n")
        else:
            print(render_executor_result_ingest_stdout(exc.outcome.summary))
        return exc.exit_code
    except ArtifactLoadError as exc:
        print(f"qa-z executor-result ingest: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z executor-result ingest: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z executor-result ingest: configuration error: {exc}")
        return 2


def handle_executor_result_dry_run(args: argparse.Namespace) -> int:
    """Run a live-free safety dry-run against one session history."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    try:
        outcome = run_executor_result_dry_run(root=root, session_ref=args.session)
        if args.json:
            print(json.dumps(outcome.summary, indent=2, sort_keys=True), end="\n")
        else:
            print(render_executor_result_dry_run_stdout(outcome.summary))
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z executor-result dry-run: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z executor-result dry-run: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z executor-result dry-run: configuration error: {exc}")
        return 2


def register_executor_result_command(
    subparsers: argparse._SubParsersAction,
) -> None:
    """Register the executor-result command."""
    executor_result_parser = subparsers.add_parser(
        "executor-result",
        help="ingest an external executor result and resume QA-Z verification",
    )
    executor_result_subparsers = executor_result_parser.add_subparsers(
        dest="executor_result_command"
    )

    executor_result_ingest_parser = executor_result_subparsers.add_parser(
        "ingest",
        help="ingest an executor result JSON and optionally rerun verification",
    )
    executor_result_ingest_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    executor_result_ingest_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    executor_result_ingest_parser.add_argument(
        "--result",
        required=True,
        help="path to a filled executor result JSON artifact",
    )
    executor_result_ingest_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable ingest summary to stdout",
    )
    executor_result_ingest_parser.set_defaults(handler=handle_executor_result_ingest)

    executor_result_dry_run_parser = executor_result_subparsers.add_parser(
        "dry-run",
        help="evaluate session executor history against the pre-live safety package",
    )
    executor_result_dry_run_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    executor_result_dry_run_parser.add_argument(
        "--session",
        required=True,
        help="repair-session id, session directory, or session.json path",
    )
    executor_result_dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable dry-run summary to stdout",
    )
    executor_result_dry_run_parser.set_defaults(handler=handle_executor_result_dry_run)
