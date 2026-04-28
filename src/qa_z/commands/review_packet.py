"""Review packet CLI command handler."""

from __future__ import annotations

import argparse
from pathlib import Path

from qa_z.artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_run_source,
)
from qa_z.commands.common import load_cli_config, resolve_cli_path
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.review_packet import (
    find_latest_contract,
    render_review_packet,
    render_run_review_packet,
    review_packet_json,
    run_review_packet_json,
    write_review_artifacts,
)


def handle_review(args: argparse.Namespace) -> int:
    """Render a review packet from a generated contract."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "review")
    if config is None:
        return 2

    try:
        if args.from_run:
            run_source = resolve_run_source(root, config, args.from_run)
            summary = load_run_summary(run_source.summary_path)
            deep_summary = load_sibling_deep_summary(run_source)
            contract_path = resolve_contract_source(
                root, config, summary=summary, explicit_contract=args.contract
            )
            contract = load_contract_context(contract_path, root)
            markdown = render_run_review_packet(
                summary=summary,
                run_source=run_source,
                contract=contract,
                root=root,
                deep_summary=deep_summary,
            )
            json_text = run_review_packet_json(
                summary=summary,
                run_source=run_source,
                contract=contract,
                root=root,
                deep_summary=deep_summary,
            )
            if args.output_dir:
                write_review_artifacts(
                    markdown, json_text, resolve_cli_path(root, args.output_dir)
                )
            if args.json:
                print(json_text, end="")
            else:
                print(markdown, end="")
            return 0

        contract_path = (
            resolve_cli_path(root, args.contract)
            if args.contract
            else find_latest_contract(root, config)
        )
        markdown = render_review_packet(contract_path, root)
        json_text = review_packet_json(contract_path, root)
        if args.output_dir:
            write_review_artifacts(
                markdown, json_text, resolve_cli_path(root, args.output_dir)
            )
        if args.json:
            print(json_text, end="")
        else:
            print(markdown, end="")
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z review: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z review: source not found: {exc}")
        return 4


def register_review_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the review command."""
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
    review_parser.add_argument(
        "--output-dir",
        help="optional directory for review.md and review.json artifacts",
    )
    review_parser.set_defaults(handler=handle_review)
