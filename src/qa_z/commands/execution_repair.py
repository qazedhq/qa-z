"""Repair-prompt CLI command handler."""

from __future__ import annotations

import argparse
from pathlib import Path

from qa_z.adapters.claude import render_claude_handoff
from qa_z.adapters.codex import render_codex_handoff
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
from qa_z.reporters.repair_prompt import (
    build_repair_packet,
    repair_packet_json,
    write_repair_artifacts,
)
from qa_z.repair_handoff import (
    build_repair_handoff,
    repair_handoff_json,
    write_repair_handoff_artifact,
)


def handle_repair_prompt(args: argparse.Namespace) -> int:
    """Render deterministic repair artifacts from a failed run."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "repair-prompt")
    if config is None:
        return 2

    try:
        run_source = resolve_run_source(root, config, args.from_run)
        summary = load_run_summary(run_source.summary_path)
        deep_summary = load_sibling_deep_summary(run_source)
        contract_path = resolve_contract_source(
            root, config, summary=summary, explicit_contract=args.contract
        )
        contract = load_contract_context(contract_path, root)
        packet = build_repair_packet(
            summary=summary,
            run_source=run_source,
            contract=contract,
            root=root,
            deep_summary=deep_summary,
        )
        handoff = build_repair_handoff(
            repair_packet=packet,
            summary=summary,
            run_source=run_source,
            root=root,
            deep_summary=deep_summary,
        )
        codex_markdown = render_codex_handoff(handoff)
        claude_markdown = render_claude_handoff(handoff)
        output_dir = (
            resolve_cli_path(root, args.output_dir)
            if args.output_dir
            else run_source.run_dir / "repair"
        )
        write_repair_artifacts(packet, output_dir)
        write_repair_handoff_artifact(handoff, output_dir)
        (output_dir / "codex.md").write_text(codex_markdown, encoding="utf-8")
        (output_dir / "claude.md").write_text(claude_markdown, encoding="utf-8")
        if args.handoff_json:
            print(repair_handoff_json(handoff), end="")
            return 0
        if args.json:
            print(repair_packet_json(packet), end="")
        elif args.adapter == "codex":
            print(codex_markdown, end="")
        elif args.adapter == "claude":
            print(claude_markdown, end="")
        else:
            print(packet.agent_prompt, end="")
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z repair-prompt: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-prompt: source not found: {exc}")
        return 4


def register_repair_prompt_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the repair-prompt command."""
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
        help="optional explicit contract path; defaults to the contract referenced by the selected run",
    )
    repair_parser.add_argument(
        "--output-dir",
        help="optional directory for repair artifacts; defaults to <run>/repair",
    )
    repair_parser.add_argument(
        "--adapter",
        choices=("legacy", "codex", "claude"),
        default="legacy",
        help="render the legacy prompt, Codex handoff, or Claude handoff",
    )
    repair_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable repair packet to stdout",
    )
    repair_parser.add_argument(
        "--handoff-json",
        action="store_true",
        help="print the machine-readable normalized repair handoff to stdout",
    )
    repair_parser.set_defaults(handler=handle_repair_prompt)
