"""Demo CLI commands."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


def handle_demo_auth_bug(args: argparse.Namespace) -> int:
    """Run the bundled auth-bug demo in an isolated temp-style directory."""
    root = Path(args.path).expanduser().resolve()
    demo_root = root / ".qa-z" / "demo" / "auth-bug"
    if demo_root.exists():
        shutil.rmtree(demo_root)
    source = Path(__file__).resolve().parents[3] / "examples" / "agent-auth-bug"
    shutil.copytree(
        source,
        demo_root,
        ignore=shutil.ignore_patterns(".qa-z", "qa", "__pycache__"),
    )
    from qa_z.cli import main as qa_z_main

    plan_exit = qa_z_main(
        [
            "plan",
            "--path",
            str(demo_root),
            "--title",
            "AI auth bug caught by QA-Z",
            "--issue",
            str(demo_root / "issue.md"),
            "--spec",
            str(demo_root / "spec.md"),
            "--slug",
            "ai-auth-bug",
            "--overwrite",
        ]
    )
    guard_exit = qa_z_main(
        [
            "guard",
            "--path",
            str(demo_root),
            "--title",
            "AI auth bug caught by QA-Z",
            "--slug",
            "ai-auth-bug",
            "--deep",
            "never",
        ]
    )
    if plan_exit != 0 or guard_exit != 0:
        return 1
    print("AI wrote a risky auth change. QA-Z caught it before merge.")
    print(f"Demo root: {demo_root}")
    print("Guard verdict: .qa-z/runs/latest/guard/verdict.json")
    print("Repair prompt: .qa-z/runs/latest/repair/codex.md")
    return 0


def handle_demo(args: argparse.Namespace) -> int:
    """Dispatch nested demo commands."""
    if hasattr(args, "demo_handler"):
        return int(args.demo_handler(args))
    print("qa-z demo: missing subcommand; run `qa-z demo --help`")
    return 2


def register_demo_command(subparsers: argparse._SubParsersAction) -> None:
    """Register demo commands."""
    demo_parser = subparsers.add_parser(
        "demo",
        help="run bundled QA-Z demos",
    )
    demo_subparsers = demo_parser.add_subparsers(dest="demo_command")
    auth_parser = demo_subparsers.add_parser(
        "auth-bug",
        help="run the deterministic auth-bug safety demo",
    )
    auth_parser.add_argument(
        "--path",
        default=".",
        help="directory where the isolated demo copy should be created",
    )
    auth_parser.set_defaults(demo_handler=handle_demo_auth_bug)
    demo_parser.set_defaults(handler=handle_demo)
