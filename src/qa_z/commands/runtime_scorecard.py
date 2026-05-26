"""Scorecard CLI command for local readiness and coverage diagnostics."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from qa_z.commands.common import resolve_cli_path
from qa_z.scorecard import STATUS_LABELS, build_scorecard

__all__ = [
    "handle_scorecard",
    "register_scorecard_command",
    "render_scorecard_markdown",
    "render_scorecard_text",
]


def handle_scorecard(args: argparse.Namespace) -> int:
    """Render a read-only readiness scorecard."""
    root = Path(args.path).expanduser().resolve()
    config_path = resolve_cli_path(root, args.config) if args.config else None
    payload = build_scorecard(
        root=root,
        config_path=config_path,
        from_run=args.from_run,
    )
    if args.json:
        rendered = json.dumps(payload, indent=2, sort_keys=False) + "\n"
    elif args.markdown:
        rendered = render_scorecard_markdown(payload)
    else:
        rendered = render_scorecard_text(payload)

    print(rendered, end="")
    if args.output:
        output_path = resolve_cli_path(root, args.output)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(
                f"qa-z scorecard: could not write --output {output_path}: {exc}",
                file=sys.stderr,
            )
            return 2
    return 0


def render_scorecard_text(payload: dict[str, Any]) -> str:
    """Render a short terminal-friendly scorecard."""
    lines = [f"QA-Z Scorecard: {payload.get('status')}"]
    dimensions = payload.get("dimensions")
    if isinstance(dimensions, list):
        lines.append("")
        for dimension in dimensions:
            if not isinstance(dimension, dict):
                continue
            status = str(dimension.get("status") or "unknown")
            label = STATUS_LABELS.get(status, status.upper())
            name = label_for_dimension(str(dimension.get("id") or "dimension"))
            lines.append(f"{label} {name}: {dimension.get('message')}")

    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "Warnings:"])
        for warning in warnings[:5]:
            lines.append(f"- {warning}")

    lines.extend(["", "Next actions:"])
    actions = payload.get("next_actions")
    if isinstance(actions, list) and actions:
        for index, action in enumerate(actions, start=1):
            lines.append(f"{index}. {format_next_action(str(action))}")
    else:
        lines.append("1. Run `qa-z summary --from-run latest`")
    return "\n".join(lines).rstrip() + "\n"


def render_scorecard_markdown(payload: dict[str, Any]) -> str:
    """Render the scorecard as Markdown."""
    lines = [
        "# QA-Z Scorecard",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Version: `{payload.get('version')}`",
        f"- Root: `{payload.get('root')}`",
        "",
        "## Dimensions",
        "",
    ]
    dimensions = payload.get("dimensions")
    if isinstance(dimensions, list):
        for dimension in dimensions:
            if not isinstance(dimension, dict):
                continue
            lines.append(
                "- "
                f"{label_for_dimension(str(dimension.get('id') or 'dimension'))}: "
                f"`{dimension.get('status')}` - {dimension.get('message')}"
            )
            suggestion = dimension.get("suggestion")
            if suggestion:
                lines.append(f"  Suggestion: {suggestion}")
    warnings = payload.get("warnings")
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)

    lines.extend(["", "## Next Actions", ""])
    actions = payload.get("next_actions")
    if isinstance(actions, list) and actions:
        lines.extend(f"{index}. `{action}`" for index, action in enumerate(actions, 1))
    else:
        lines.append("1. `qa-z summary --from-run latest`")
    return "\n".join(lines).rstrip() + "\n"


def format_next_action(action: str) -> str:
    """Render command-like actions with a Run prefix and prose actions plainly."""
    command_prefixes = ("qa-z ", "python ", "python -m ", "pip ", "pipx ", "uv ")
    if action.startswith(command_prefixes):
        return f"Run `{action}`"
    return action


def label_for_dimension(dimension_id: str) -> str:
    """Return a concise human label for a scorecard dimension id."""
    labels = {
        "project_config": "project config",
        "profile": "profile",
        "fast_checks": "fast checks",
        "deep_semgrep": "deep/Semgrep",
        "benchmark_corpus": "benchmark corpus",
        "repair_prompt": "repair prompt",
        "verify": "verify",
        "github_action": "GitHub Action",
        "installed_package_smoke": "installed package smoke",
        "evidence_freshness": "evidence freshness",
    }
    return labels.get(dimension_id, dimension_id.replace("_", " "))


def register_scorecard_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the scorecard command."""
    scorecard_parser = subparsers.add_parser(
        "scorecard",
        help="summarize QA-Z readiness and coverage signals",
    )
    scorecard_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and QA-Z artifacts",
    )
    scorecard_parser.add_argument("--config", help="optional explicit config path")
    scorecard_parser.add_argument(
        "--from-run",
        default="latest",
        help="run root, fast directory, summary.json, or latest",
    )
    scorecard_parser.add_argument(
        "--json",
        action="store_true",
        help="print stable machine-readable JSON",
    )
    scorecard_parser.add_argument(
        "--markdown",
        action="store_true",
        help="print a Markdown scorecard",
    )
    scorecard_parser.add_argument(
        "--output",
        help="optional path to write the rendered scorecard",
    )
    scorecard_parser.set_defaults(handler=handle_scorecard)
