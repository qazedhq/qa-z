"""Fast and deep execution CLI command handlers."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    write_latest_run_manifest,
)
from qa_z.commands.common import load_cli_config, resolve_cli_path
from qa_z.config import get_nested
from qa_z.reporters.run_summary import write_run_summary_artifacts
from qa_z.reporters.sarif import write_sarif_artifact
from qa_z.runners.deep import run_deep
from qa_z.runners.fast import run_fast, summary_json


def handle_fast(args: argparse.Namespace) -> int:
    """Run deterministic fast checks."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "fast")
    if config is None:
        return 2

    contract_path = resolve_cli_path(root, args.contract) if args.contract else None
    output_dir = resolve_cli_path(root, args.output_dir) if args.output_dir else None

    try:
        run = run_fast(
            root=root,
            config=config,
            contract_path=contract_path,
            diff_path=resolve_cli_path(root, args.diff) if args.diff else None,
            output_dir=output_dir,
            strict_no_tests=args.strict_no_tests,
            selection_mode=resolve_fast_selection_mode(config, args.selection),
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"qa-z fast: configuration error: {exc}")
        return 2

    artifact_dir = Path(run.summary.artifact_dir or "")
    if not artifact_dir.is_absolute():
        artifact_dir = root / artifact_dir
    summary_path = write_run_summary_artifacts(run.summary, artifact_dir)
    write_latest_run_manifest(root, config, artifact_dir.parent)

    if args.json:
        print(summary_json(run.summary), end="")
    else:
        print(
            render_fast_stdout(
                run.summary.status, run.summary.contract_path, summary_path, root
            )
        )

    return run.exit_code


def register_fast_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the fast command."""
    fast_parser = subparsers.add_parser(
        "fast",
        help="run fast deterministic checks",
    )
    fast_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and contract output directories",
    )
    fast_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    fast_parser.add_argument(
        "--contract",
        help="optional explicit contract path; defaults to the newest contract in the configured output directory",
    )
    fast_parser.add_argument(
        "--output-dir",
        help="optional run artifact directory; defaults to fast.output_dir plus a UTC timestamp",
    )
    fast_parser.add_argument(
        "--selection",
        choices=("full", "smart"),
        default=None,
        help="check selection mode; defaults to fast.selection.default_mode or full",
    )
    fast_parser.add_argument(
        "--diff",
        help="optional diff excerpt or patch file for smart selection",
    )
    fast_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable run summary to stdout",
    )
    fast_parser.add_argument(
        "--strict-no-tests",
        action="store_true",
        help="treat pytest no-tests exit code as a failure",
    )
    fast_parser.set_defaults(handler=handle_fast)


def handle_deep(args: argparse.Namespace) -> int:
    """Create deep-runner artifacts."""
    if args.from_run and args.output_dir:
        print(
            "qa-z deep: argument error: --from-run and --output-dir cannot be "
            "combined; use --from-run to attach to a fast run or --output-dir "
            "to create a standalone deep run."
        )
        return 2

    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "deep")
    if config is None:
        return 2

    try:
        run = run_deep(
            root=root,
            config=config,
            output_dir=resolve_cli_path(root, args.output_dir)
            if args.output_dir
            else None,
            from_run=args.from_run,
            diff_path=resolve_cli_path(root, args.diff) if args.diff else None,
            selection_mode=resolve_deep_selection_mode(config, args.selection),
        )
    except ArtifactLoadError as exc:
        print(f"qa-z deep: artifact error: {exc}")
        return 2
    except ArtifactSourceNotFound as exc:
        print(f"qa-z deep: source not found: {exc}")
        return 4
    except (FileNotFoundError, ValueError) as exc:
        print(f"qa-z deep: configuration error: {exc}")
        return 2

    summary_path = write_run_summary_artifacts(run.summary, run.resolution.deep_dir)
    write_sarif_artifact(run.summary, run.resolution.deep_dir / "results.sarif")
    if args.sarif_output:
        write_sarif_artifact(run.summary, resolve_cli_path(root, args.sarif_output))

    if args.json:
        print(summary_json(run.summary), end="")
    else:
        print(render_deep_stdout(run.summary.status, summary_path, root))

    return run.exit_code


def register_deep_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the deep command."""
    deep_parser = subparsers.add_parser(
        "deep",
        help="run deeper risk-oriented checks",
    )
    deep_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and contract output directories",
    )
    deep_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    deep_parser.add_argument(
        "--output-dir",
        help="optional deep artifact directory; defaults to latest fast run or a new UTC timestamped run",
    )
    deep_parser.add_argument(
        "--from-run",
        help="optional run root, fast directory, summary.json, or latest fast run artifact to attach deep artifacts to",
    )
    deep_parser.add_argument(
        "--selection",
        choices=("full", "smart"),
        default=None,
        help="deep selection mode; defaults to deep.selection.default_mode or full",
    )
    deep_parser.add_argument(
        "--diff",
        help="optional diff excerpt or patch file for smart deep selection",
    )
    deep_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable deep summary to stdout",
    )
    deep_parser.add_argument(
        "--sarif-output",
        help="optional file path for a copy of the generated SARIF report",
    )
    deep_parser.set_defaults(handler=handle_deep)


def resolve_fast_selection_mode(config: dict[str, Any], explicit: str | None) -> str:
    """Resolve the fast selection mode from CLI input or config default."""
    if explicit:
        return explicit
    configured = str(
        get_nested(config, "fast", "selection", "default_mode", default="full")
    )
    return configured if configured in {"full", "smart"} else "full"


def resolve_deep_selection_mode(config: dict[str, Any], explicit: str | None) -> str:
    """Resolve the deep selection mode from CLI input or config default."""
    if explicit:
        return explicit
    configured = str(
        get_nested(config, "deep", "selection", "default_mode", default="full")
    )
    return configured if configured in {"full", "smart"} else "full"


def render_fast_stdout(
    status: str, contract_path: str | None, summary_path: Path, root: Path
) -> str:
    """Render the default human CLI output for qa-z fast."""
    try:
        relative_summary = summary_path.relative_to(root).as_posix()
    except ValueError:
        relative_summary = str(summary_path)
    contract = contract_path or "none"
    return "\n".join(
        [
            f"qa-z fast: {status}",
            f"Contract: {contract}",
            f"Summary: {relative_summary}",
        ]
    )


def render_deep_stdout(status: str, summary_path: Path, root: Path) -> str:
    """Render the default human CLI output for qa-z deep."""
    try:
        relative_summary = summary_path.relative_to(root).as_posix()
    except ValueError:
        relative_summary = str(summary_path)
    return "\n".join(
        [
            f"qa-z deep: {status}",
            f"Summary: {relative_summary}",
        ]
    )
