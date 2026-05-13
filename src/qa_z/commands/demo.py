"""Demo CLI commands."""

from __future__ import annotations

import argparse
from importlib.abc import Traversable
from importlib.resources import files
from pathlib import Path
import shutil
from textwrap import dedent


IGNORED_DEMO_NAMES = {".qa-z", "qa", "__pycache__"}
AUTH_BUG_DEMO_CONFIG = dedent(
    """
    project:
      name: qa-z-agent-auth-bug-demo
      languages:
        - python

    contracts:
      output_dir: qa/contracts

    fast:
      output_dir: .qa-z/runs
      fail_on_missing_tool: true
      checks:
        - id: auth_policy
          enabled: true
          kind: test
          run:
            - python
            - -c
            - |
              from app.auth import Invoice, can_view_invoice
              invoice = Invoice(id="inv_123", owner_id="user_1")
              assert can_view_invoice("user_1", invoice)
              assert can_view_invoice("support_admin", invoice, is_admin=True)
              assert not can_view_invoice("user_2", invoice), "can_view_invoice allowed a non-owner"

    deep:
      fail_on_missing_tool: true
      checks: []
    """
).lstrip()


def handle_demo_auth_bug(args: argparse.Namespace) -> int:
    """Run the bundled auth-bug demo in an isolated temp-style directory."""
    root = Path(args.path).expanduser().resolve()
    demo_root = root / ".qa-z" / "demo" / "auth-bug"
    try:
        if demo_root.exists():
            shutil.rmtree(demo_root)
        copy_resource_tree(demo_auth_bug_resource(), demo_root)
        demo_config = write_demo_runtime_config(demo_root)
    except OSError as exc:
        print(
            "qa-z demo auth-bug: artifact write error: "
            f"could not prepare demo artifacts: {exc}"
        )
        return 2
    from qa_z.cli import main as qa_z_main

    plan_exit = qa_z_main(
        [
            "plan",
            "--path",
            str(demo_root),
            "--config",
            str(demo_config),
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
            "--config",
            str(demo_config),
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
    print("Demo config: qa-z.demo.yaml")
    print("Guard verdict: .qa-z/runs/latest/guard/verdict.json")
    print("Repair prompt: .qa-z/runs/latest/repair/codex.md")
    print("Next:")
    print(f"  cd {demo_root}")
    print("  qa-z guard --from-run latest --adapter codex")
    print("  qa-z repair-prompt --from-run latest --adapter codex")
    return 0


def demo_auth_bug_resource() -> Traversable:
    """Return the packaged auth-bug demo resource directory."""
    return files("qa_z.templates").joinpath("examples").joinpath("agent-auth-bug")


def copy_resource_tree(source: Traversable, destination: Path) -> None:
    """Copy a packaged resource directory to the filesystem."""
    if not source.is_dir():
        raise FileNotFoundError(f"missing packaged demo resource: {source}")
    try:
        destination.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise OSError(
            f"could not create demo resource directory {destination}: {exc}"
        ) from exc
    for child in source.iterdir():
        if child.name in IGNORED_DEMO_NAMES:
            continue
        target = destination / child.name
        if child.is_dir():
            copy_resource_tree(child, target)
        else:
            write_resource_file(target, child.read_bytes())


def write_resource_file(path: Path, content: bytes) -> None:
    """Write one packaged demo resource with path-aware errors."""
    try:
        path.write_bytes(content)
    except OSError as exc:
        raise OSError(f"could not write demo resource {path}: {exc}") from exc


def write_demo_runtime_config(demo_root: Path) -> Path:
    """Write a dependency-light config for the installed demo command."""
    config_path = demo_root / "qa-z.demo.yaml"
    try:
        config_path.write_text(AUTH_BUG_DEMO_CONFIG, encoding="utf-8", newline="\n")
    except OSError as exc:
        raise OSError(
            f"could not write demo runtime config {config_path}: {exc}"
        ) from exc
    return config_path


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
