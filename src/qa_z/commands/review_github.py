"""GitHub summary CLI command handler."""

from __future__ import annotations

import argparse
from pathlib import Path

from qa_z.artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
)
from qa_z.commands.common import load_cli_config, resolve_cli_path
from qa_z.commands.review_github_context import load_github_summary_context
from qa_z.reporters.github_summary import render_github_summary


def handle_github_summary(args: argparse.Namespace) -> int:
    """Render compact Markdown for GitHub Actions job summaries."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "github-summary")
    if config is None:
        return 2

    try:
        summary_context = load_github_summary_context(
            root=root,
            config=config,
            from_run=args.from_run,
            from_session=args.from_session,
        )
        markdown = render_github_summary(
            summary=summary_context.summary,
            run_source=summary_context.run_source,
            root=root,
            deep_summary=summary_context.deep_summary,
            publish_summary=summary_context.publish_summary,
        )
        if args.output:
            output_path = resolve_cli_path(root, args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
        print(markdown, end="")
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z github-summary: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z github-summary: source not found: {exc}")
        return 4


def register_github_summary_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the github-summary command."""
    github_summary_parser = subparsers.add_parser(
        "github-summary",
        help="render compact Markdown for a GitHub Actions job summary",
    )
    github_summary_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    github_summary_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    github_summary_parser.add_argument(
        "--from-run",
        default="latest",
        help="run root, fast directory, summary.json, or latest fast run artifact",
    )
    github_summary_parser.add_argument(
        "--from-session",
        help=(
            "optional repair-session id, directory, or session.json whose "
            "outcome should be included"
        ),
    )
    github_summary_parser.add_argument(
        "--output",
        help="optional file path for the rendered GitHub summary Markdown",
    )
    github_summary_parser.set_defaults(handler=handle_github_summary)
