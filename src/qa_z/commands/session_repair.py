"""Repair-session CLI command handlers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound
from qa_z.commands.common import load_cli_config
from qa_z.repair_session import (
    create_repair_session,
    load_repair_session,
    load_session_dry_run_summary,
    render_session_start_stdout,
    render_session_status_with_dry_run,
    render_session_verify_stdout,
    session_status_dict,
    session_summary_json,
)
from qa_z.verification import verify_exit_code


def handle_repair_session_start(args: argparse.Namespace) -> int:
    """Create a local repair-session from a baseline run."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "repair-session start")
    if config is None:
        return 2

    try:
        result = create_repair_session(
            root=root,
            config=config,
            baseline_run=args.baseline_run,
            session_id=args.session_id,
        )
        print(render_session_start_stdout(result.session))
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z repair-session start: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-session start: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z repair-session start: configuration error: {exc}")
        return 2


def handle_repair_session_status(args: argparse.Namespace) -> int:
    """Print the current state of a repair-session."""
    root = Path(args.path).expanduser().resolve()

    try:
        session = load_repair_session(root, args.session)
        dry_run_summary = load_session_dry_run_summary(session, root)
        if args.json:
            print(
                json.dumps(
                    session_status_dict(session, dry_run_summary=dry_run_summary),
                    indent=2,
                    sort_keys=True,
                ),
                end="\n",
            )
        else:
            print(
                render_session_status_with_dry_run(
                    session,
                    dry_run_summary=dry_run_summary,
                )
            )
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z repair-session status: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-session status: source not found: {exc}")
        return 4


def handle_repair_session_verify(args: argparse.Namespace) -> int:
    """Verify a repair-session with an existing or freshly rerun candidate."""
    from qa_z.executor_ingest import verify_repair_session

    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "repair-session verify")
    if config is None:
        return 2

    if bool(args.candidate_run) == bool(args.rerun):
        print(
            "qa-z repair-session verify: configuration error: provide exactly one "
            "of --candidate-run or --rerun."
        )
        return 2

    try:
        session = load_repair_session(root, args.session)
        updated, summary, comparison = verify_repair_session(
            session=session,
            root=root,
            config=config,
            candidate_run=args.candidate_run,
            rerun=args.rerun,
            rerun_output_dir=args.rerun_output_dir,
            strict_no_tests=args.strict_no_tests,
            output_dir=args.output_dir,
        )

        if args.json:
            print(session_summary_json(summary), end="")
        else:
            print(render_session_verify_stdout(updated, summary))
        return verify_exit_code(comparison.verdict)
    except ArtifactLoadError as exc:
        print(f"qa-z repair-session verify: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-session verify: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z repair-session verify: configuration error: {exc}")
        return 2


def register_repair_session_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the repair-session command."""
    repair_session_parser = subparsers.add_parser(
        "repair-session",
        help="create and verify local repair workflow sessions",
    )
    repair_session_subparsers = repair_session_parser.add_subparsers(
        dest="repair_session_command"
    )

    repair_session_start_parser = repair_session_subparsers.add_parser(
        "start",
        help="create a repair session from a baseline run",
    )
    repair_session_start_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    repair_session_start_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    repair_session_start_parser.add_argument(
        "--baseline-run",
        required=True,
        help="baseline run root, fast directory, summary.json, or latest",
    )
    repair_session_start_parser.add_argument(
        "--session-id",
        help="optional stable session id; defaults to a UTC timestamp plus suffix",
    )
    repair_session_start_parser.set_defaults(handler=handle_repair_session_start)

    repair_session_status_parser = repair_session_subparsers.add_parser(
        "status",
        help="print repair-session state and artifact paths",
    )
    repair_session_status_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains .qa-z/sessions",
    )
    repair_session_status_parser.add_argument(
        "--session",
        required=True,
        help="session id, session directory, or session.json path",
    )
    repair_session_status_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable session manifest to stdout",
    )
    repair_session_status_parser.set_defaults(handler=handle_repair_session_status)

    repair_session_verify_parser = repair_session_subparsers.add_parser(
        "verify",
        help="verify a repair session against a candidate run",
    )
    repair_session_verify_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and session artifacts",
    )
    repair_session_verify_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    repair_session_verify_parser.add_argument(
        "--session",
        required=True,
        help="session id, session directory, or session.json path",
    )
    repair_session_candidate_group = (
        repair_session_verify_parser.add_mutually_exclusive_group()
    )
    repair_session_candidate_group.add_argument(
        "--candidate-run",
        help="candidate run root, fast directory, summary.json, or latest",
    )
    repair_session_candidate_group.add_argument(
        "--rerun",
        action="store_true",
        help="run qa-z fast and qa-z deep into the session candidate directory",
    )
    repair_session_verify_parser.add_argument(
        "--rerun-output-dir",
        help="optional run directory for a --rerun candidate",
    )
    repair_session_verify_parser.add_argument(
        "--output-dir",
        help="optional verify artifact directory; defaults to session/verify",
    )
    repair_session_verify_parser.add_argument(
        "--strict-no-tests",
        action="store_true",
        help="with --rerun, treat pytest no-tests exit code as a failure",
    )
    repair_session_verify_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable session outcome summary to stdout",
    )
    repair_session_verify_parser.set_defaults(handler=handle_repair_session_verify)
