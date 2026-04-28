"""Init bootstrap CLI command handler."""

from __future__ import annotations

import argparse
from importlib.resources import (
    files,
)  # nosemgrep: python.lang.compatibility.python37.python37-compatibility-importlib2
from pathlib import Path
from typing import Any

import yaml

from qa_z.commands.common import (
    format_relative_path,
    write_text_if_missing,
)
from qa_z.config import CONTRACTS_README, EXAMPLE_CONFIG

INIT_PROFILES = ("default", "python", "typescript", "monorepo")

GITHUB_WORKFLOW = """name: QA-Z

on:
  pull_request:
  push:
    branches:
      - main

jobs:
  qa-z:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install -e .[dev]
      - run: python -m qa_z fast
"""


def handle_init(args: argparse.Namespace) -> int:
    """Bootstrap a repository with starter QA-Z files."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    config_path = root / "qa-z.yaml"
    contracts_readme = root / "qa" / "contracts" / "README.md"
    agent_templates = (
        (root / "AGENTS.md", template_text("AGENTS.md")),
        (root / "CLAUDE.md", template_text("CLAUDE.md")),
    )
    github_workflow = root / ".github" / "workflows" / "qa-z.yml"

    created: list[Path] = []
    skipped: list[Path] = []

    for path, content in (
        (config_path, profile_config(args.profile)),
        (contracts_readme, CONTRACTS_README),
    ):
        if write_text_if_missing(path, content):
            created.append(path)
        else:
            skipped.append(path)

    if args.with_agent_templates:
        for path, content in agent_templates:
            if write_text_if_missing(path, content):
                created.append(path)
            else:
                skipped.append(path)

    if args.with_github_workflow:
        if write_text_if_missing(github_workflow, GITHUB_WORKFLOW):
            created.append(github_workflow)
        else:
            skipped.append(github_workflow)

    print(f"Initialized QA-Z bootstrap in {root}")
    for path in created:
        print(f"created: {format_relative_path(path, root)}")
    for path in skipped:
        print(f"skipped: {format_relative_path(path, root)}")

    if not created:
        print("Nothing new was written because the starter files already exist.")

    return 0


def template_text(name: str) -> str:
    """Load a packaged starter template."""
    return files("qa_z.templates").joinpath(name).read_text(encoding="utf-8")


def profile_config(profile: str) -> str:
    """Return bootstrap config tailored for a starter profile."""
    if profile == "default":
        return EXAMPLE_CONFIG

    loaded = yaml.safe_load(EXAMPLE_CONFIG)
    if not isinstance(loaded, dict):
        return EXAMPLE_CONFIG
    config: dict[str, Any] = loaded

    project = config.setdefault("project", {})
    if isinstance(project, dict):
        if profile == "python":
            project["languages"] = ["python"]
        elif profile == "typescript":
            project["languages"] = ["typescript"]
        elif profile == "monorepo":
            project["languages"] = ["python", "typescript"]

    fast = config.setdefault("fast", {})
    if isinstance(fast, dict):
        checks = fast.get("checks")
        if profile == "python":
            fast["checks"] = filter_check_items(checks, "py_")
        elif profile == "typescript":
            fast["checks"] = filter_check_items(checks, "ts_")
        elif profile == "monorepo":
            selection = fast.setdefault("selection", {})
            if isinstance(selection, dict):
                selection["default_mode"] = "smart"

    return yaml.safe_dump(config, sort_keys=False)


def filter_check_items(items: Any, prefix: str) -> list[Any]:
    """Filter config check items by id prefix."""
    if not isinstance(items, list):
        return []
    filtered: list[Any] = []
    for item in items:
        if isinstance(item, str) and item.startswith(prefix):
            filtered.append(item)
            continue
        if isinstance(item, dict) and str(item.get("id", "")).startswith(prefix):
            filtered.append(item)
    return filtered


def register_init_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the init command."""
    init_parser = subparsers.add_parser(
        "init",
        help="write a starter qa-z.yaml and contracts workspace",
    )
    init_parser.add_argument(
        "--path",
        default=".",
        help="directory to initialize, defaults to the current working directory",
    )
    init_parser.add_argument(
        "--profile",
        choices=INIT_PROFILES,
        default="default",
        help="starter config profile to write",
    )
    init_parser.add_argument(
        "--with-agent-templates",
        action="store_true",
        help="write AGENTS.md and CLAUDE.md starter templates",
    )
    init_parser.add_argument(
        "--with-github-workflow",
        action="store_true",
        help="write a starter GitHub Actions workflow for QA-Z",
    )
    init_parser.set_defaults(handler=handle_init)
