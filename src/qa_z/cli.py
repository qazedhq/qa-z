"""Command line interface for QA-Z."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from .artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_run_source,
)
from .config import COMMAND_GUIDANCE, CONTRACTS_README, EXAMPLE_CONFIG, load_config
from .planner.contracts import plan_contract
from .reporters.repair_prompt import (
    build_repair_packet,
    repair_packet_json,
    write_repair_artifacts,
)
from .reporters.run_summary import write_run_summary_artifacts
from .reporters.review_packet import (
    find_latest_contract,
    render_review_packet,
    render_run_review_packet,
    review_packet_json,
    run_review_packet_json,
)
from .runners.fast import run_fast, summary_json


def write_text_if_missing(path: Path, content: str) -> bool:
    """Create a text file only when it does not exist yet."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def format_relative_path(path: Path, root: Path) -> str:
    """Render a stable relative path for CLI output."""
    return path.relative_to(root).as_posix()


def handle_init(args: argparse.Namespace) -> int:
    """Bootstrap a repository with starter QA-Z files."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    config_path = root / "qa-z.yaml"
    contracts_readme = root / "qa" / "contracts" / "README.md"

    created = []
    skipped = []

    for path, content in (
        (config_path, EXAMPLE_CONFIG),
        (contracts_readme, CONTRACTS_README),
    ):
        if write_text_if_missing(path, content):
            created.append(path)
        else:
            skipped.append(path)

    print(f"Initialized QA-Z bootstrap in {root}")
    for path in created:
        print(f"created: {format_relative_path(path, root)}")
    for path in skipped:
        print(f"skipped: {format_relative_path(path, root)}")

    if not created:
        print("Nothing new was written because the starter files already exist.")

    return 0


def handle_plan(args: argparse.Namespace) -> int:
    """Generate a QA contract draft from local context files."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config_path = Path(args.config).expanduser().resolve() if args.config else None
    config = load_config(root, config_path=config_path)

    contract_path, created = plan_contract(
        root=root,
        config=config,
        title=args.title,
        slug=args.slug,
        issue_path=Path(args.issue).expanduser().resolve() if args.issue else None,
        spec_path=Path(args.spec).expanduser().resolve() if args.spec else None,
        diff_path=Path(args.diff).expanduser().resolve() if args.diff else None,
        overwrite=args.overwrite,
    )

    relative_contract_path = format_relative_path(contract_path, root)
    status = "created contract" if created else "kept existing contract"
    print(f"{status}: {relative_contract_path}")
    return 0


def handle_review(args: argparse.Namespace) -> int:
    """Render a review packet from a generated contract."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config_path = Path(args.config).expanduser().resolve() if args.config else None
    config = load_config(root, config_path=config_path)

    try:
        if args.from_run:
            run_source = resolve_run_source(root, config, args.from_run)
            summary = load_run_summary(run_source.summary_path)
            contract_path = resolve_contract_source(
                root, config, summary=summary, explicit_contract=args.contract
            )
            contract = load_contract_context(contract_path, root)
            if args.json:
                print(
                    run_review_packet_json(
                        summary=summary,
                        run_source=run_source,
                        contract=contract,
                        root=root,
                    ),
                    end="",
                )
            else:
                print(
                    render_run_review_packet(
                        summary=summary,
                        run_source=run_source,
                        contract=contract,
                        root=root,
                    ),
                    end="",
                )
            return 0

        if args.contract:
            contract_path = resolve_cli_path(root, args.contract)
        else:
            contract_path = find_latest_contract(root, config)
        if args.json:
            print(review_packet_json(contract_path, root), end="")
        else:
            print(render_review_packet(contract_path, root), end="")
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z review: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z review: source not found: {exc}")
        return 4


def handle_fast(args: argparse.Namespace) -> int:
    """Run deterministic fast checks."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config_path = Path(args.config).expanduser().resolve() if args.config else None
    config = load_config(root, config_path=config_path)

    contract_path = resolve_cli_path(root, args.contract) if args.contract else None
    output_dir = resolve_cli_path(root, args.output_dir) if args.output_dir else None

    try:
        run = run_fast(
            root=root,
            config=config,
            contract_path=contract_path,
            output_dir=output_dir,
            strict_no_tests=args.strict_no_tests,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"qa-z fast: configuration error: {exc}")
        return 2

    artifact_dir = Path(run.summary.artifact_dir or "")
    if not artifact_dir.is_absolute():
        artifact_dir = root / artifact_dir
    summary_path = write_run_summary_artifacts(run.summary, artifact_dir)

    if args.json:
        print(summary_json(run.summary), end="")
    else:
        print(
            render_fast_stdout(
                run.summary.status, run.summary.contract_path, summary_path, root
            )
        )

    return run.exit_code


def handle_repair_prompt(args: argparse.Namespace) -> int:
    """Render deterministic repair artifacts from a failed run."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config_path = Path(args.config).expanduser().resolve() if args.config else None
    config = load_config(root, config_path=config_path)

    try:
        run_source = resolve_run_source(root, config, args.from_run)
        summary = load_run_summary(run_source.summary_path)
        contract_path = resolve_contract_source(
            root, config, summary=summary, explicit_contract=args.contract
        )
        contract = load_contract_context(contract_path, root)
        packet = build_repair_packet(
            summary=summary,
            run_source=run_source,
            contract=contract,
            root=root,
        )
        output_dir = (
            resolve_cli_path(root, args.output_dir)
            if args.output_dir
            else run_source.run_dir / "repair"
        )
        write_repair_artifacts(packet, output_dir)
        if args.json:
            print(repair_packet_json(packet), end="")
        else:
            print(packet.agent_prompt, end="")
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z repair-prompt: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-prompt: source not found: {exc}")
        return 4


def handle_placeholder(args: argparse.Namespace) -> int:
    """Render roadmap guidance for a scaffolded command."""
    print(COMMAND_GUIDANCE[args.command])
    return 0


def resolve_cli_path(root: Path, value: str) -> Path:
    """Resolve a CLI path relative to the project root when it is not absolute."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


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


def build_parser() -> argparse.ArgumentParser:
    """Build the root CLI parser."""
    parser = argparse.ArgumentParser(
        prog="qa-z",
        description="QA-Z is a QA control plane scaffold for coding agents.",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser(
        "init",
        help="write a starter qa-z.yaml and contracts workspace",
    )
    init_parser.add_argument(
        "--path",
        default=".",
        help="directory to initialize, defaults to the current working directory",
    )
    init_parser.set_defaults(handler=handle_init)

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
        required=True,
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

    review_parser = subparsers.add_parser(
        "review",
        help="render a review packet from a generated contract",
    )
    review_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and contract output directories",
    )
    review_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    review_parser.add_argument(
        "--contract",
        help="optional explicit contract path; defaults to the newest contract in the configured output directory",
    )
    review_parser.add_argument(
        "--from-run",
        help="optional run root, fast directory, summary.json, or latest fast run artifact",
    )
    review_parser.add_argument(
        "--json",
        action="store_true",
        help="print a machine-readable review packet to stdout",
    )
    review_parser.set_defaults(handler=handle_review)

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

    repair_parser = subparsers.add_parser(
        "repair-prompt",
        help="emit an agent-friendly repair prompt",
    )
    repair_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    repair_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    repair_parser.add_argument(
        "--from-run",
        default="latest",
        help="run root, fast directory, summary.json, or latest fast run artifact",
    )
    repair_parser.add_argument(
        "--contract",
        help="optional explicit contract path overriding the run summary contract",
    )
    repair_parser.add_argument(
        "--output-dir",
        help="optional repair artifact directory; defaults to source run/repair",
    )
    repair_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable repair packet to stdout",
    )
    repair_parser.set_defaults(handler=handle_repair_prompt)

    for command, help_text in (("deep", "run deeper risk-oriented checks"),):
        subparser = subparsers.add_parser(command, help=help_text)
        subparser.set_defaults(command=command, handler=handle_placeholder)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    return int(args.handler(args))
