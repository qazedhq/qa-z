"""Verification CLI command handlers."""

from __future__ import annotations

import argparse
from pathlib import Path

from qa_z.artifacts import ArtifactLoadError, ArtifactSourceNotFound
from qa_z.commands.common import format_relative_path, load_cli_config, resolve_cli_path
from qa_z.executor_ingest import create_verify_candidate_run
from qa_z.verification import (
    VerificationArtifactPaths,
    comparison_json,
    compare_verification_runs,
    load_verification_run,
    verify_exit_code,
    write_verification_artifacts,
)


def handle_verify(args: argparse.Namespace) -> int:
    """Compare a baseline run against a post-repair candidate run."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "verify")
    if config is None:
        return 2

    if bool(args.candidate_run) == bool(args.rerun):
        print(
            "qa-z verify: configuration error: provide exactly one of "
            "--candidate-run or --rerun."
        )
        return 2

    try:
        baseline, _baseline_source = load_verification_run(
            root=root,
            config=config,
            from_run=args.baseline_run,
        )
        if args.rerun:
            rerun_output_dir = (
                resolve_cli_path(root, args.rerun_output_dir)
                if args.rerun_output_dir
                else root / ".qa-z" / "runs" / "candidate"
            )
            candidate_run = create_verify_candidate_run(
                root=root,
                config=config,
                rerun_output_dir=rerun_output_dir,
                strict_no_tests=args.strict_no_tests,
                baseline=baseline,
            )
        else:
            candidate_run = args.candidate_run

        candidate, candidate_source = load_verification_run(
            root=root,
            config=config,
            from_run=candidate_run,
        )
        comparison = compare_verification_runs(baseline, candidate)
        output_dir = (
            resolve_cli_path(root, args.output_dir)
            if args.output_dir
            else candidate_source.run_dir / "verify"
        )
        paths = write_verification_artifacts(comparison, output_dir)

        if args.json:
            print(comparison_json(comparison), end="")
        else:
            print(render_verify_stdout(comparison.verdict, paths, root))
        return verify_exit_code(comparison.verdict)
    except ArtifactLoadError as exc:
        print(f"qa-z verify: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z verify: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z verify: configuration error: {exc}")
        return 2


def register_verify_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the verify command."""
    verify_parser = subparsers.add_parser(
        "verify",
        help="compare a baseline run against a post-repair candidate run",
    )
    verify_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    verify_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    verify_parser.add_argument(
        "--baseline-run",
        required=True,
        help="baseline run root, fast directory, summary.json, or latest",
    )
    candidate_group = verify_parser.add_mutually_exclusive_group()
    candidate_group.add_argument(
        "--candidate-run",
        help="candidate run root, fast directory, summary.json, or latest",
    )
    candidate_group.add_argument(
        "--rerun",
        action="store_true",
        help="run qa-z fast and qa-z deep to create a candidate before comparing",
    )
    verify_parser.add_argument(
        "--rerun-output-dir",
        help="optional run directory for --rerun candidate artifacts",
    )
    verify_parser.add_argument(
        "--output-dir",
        help="optional verify artifact directory; defaults to candidate-run/verify",
    )
    verify_parser.add_argument(
        "--strict-no-tests",
        action="store_true",
        help="with --rerun, treat pytest no-tests exit code as a failure",
    )
    verify_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable verification comparison to stdout",
    )
    verify_parser.set_defaults(handler=handle_verify)


def render_verify_stdout(
    verdict: str, paths: VerificationArtifactPaths, root: Path
) -> str:
    """Render the default human CLI output for qa-z verify."""
    return "\n".join(
        [
            f"qa-z verify: {verdict}",
            f"Summary: {format_relative_path(paths.summary_path, root)}",
            f"Compare: {format_relative_path(paths.compare_path, root)}",
            f"Report: {format_relative_path(paths.report_path, root)}",
        ]
    )
