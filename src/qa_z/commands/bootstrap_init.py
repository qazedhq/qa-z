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
from qa_z.profile_detection import (
    ProfileDetectionResult,
    detect_profile,
)

INIT_PROFILES = (
    "default",
    "python",
    "typescript",
    "nextjs",
    "monorepo",
    "mixed",
    "unknown",
    "auto",
)

GITHUB_WORKFLOW = """name: QA-Z

on:
  pull_request:
  push:
    branches:
      - main

permissions:
  contents: read

jobs:
  qa-z:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          persist-credentials: false
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install QA-Z
        run: python -m pip install "git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha"
      - name: Validate QA-Z config
        run: python -m qa_z doctor --json
      - name: Run QA-Z fast gate
        run: python -m qa_z fast --json
"""


def handle_init(args: argparse.Namespace) -> int:
    """Bootstrap a repository with starter QA-Z files."""
    root = Path(args.path).expanduser().resolve()
    selected_profile = args.profile
    detection: ProfileDetectionResult | None = None
    if args.profile == "auto":
        detection = detect_profile(root)
        selected_profile = detection.profile

    config_path = root / "qa-z.yaml"
    contracts_readme = root / "qa" / "contracts" / "README.md"
    agent_templates = (
        (root / "AGENTS.md", template_text("AGENTS.md")),
        (root / "CLAUDE.md", template_text("CLAUDE.md")),
    )
    github_workflow = root / ".github" / "workflows" / "qa-z.yml"

    planned: list[tuple[Path, str]] = [
        (config_path, profile_config(selected_profile)),
        (contracts_readme, CONTRACTS_README),
    ]
    if args.with_agent_templates:
        planned.extend(agent_templates)
    if args.with_github_workflow:
        planned.append((github_workflow, GITHUB_WORKFLOW))

    if detection is not None or args.explain:
        if detection is None:
            detection = detect_profile(root)
        render_profile_detection(detection)

    if args.dry_run:
        print(f"QA-Z init dry run in {root}")
        for path, _content in planned:
            action = "would skip" if path.exists() else "would write"
            print(f"{action}: {format_relative_path(path, root)}")
        return 0

    root.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    skipped: list[Path] = []

    try:
        for path, content in planned:
            if write_text_if_missing(path, content):
                created.append(path)
            else:
                skipped.append(path)
    except OSError as exc:
        print(
            f"qa-z init: artifact write error: could not write bootstrap files: {exc}"
        )
        return 2

    print(f"Initialized QA-Z bootstrap in {root}")
    for path in created:
        print(f"created: {format_relative_path(path, root)}")
    for path in skipped:
        print(f"skipped: {format_relative_path(path, root)}")

    if not created:
        print("Nothing new was written because the starter files already exist.")

    return 0


def render_profile_detection(detection: ProfileDetectionResult) -> None:
    """Print the human explanation for auto profile detection."""
    evidence = ", ".join(detection.evidence_files) or "none"
    assumptions = ", ".join(detection.activated_check_assumptions)
    print(f"QA-Z init profile detection: {detection.profile}")
    print(f"confidence: {detection.confidence}")
    print(f"evidence: {evidence}")
    print(f"activated checks: {assumptions}")
    for warning in detection.warnings:
        print(f"warning: {warning}")
    print(f"next command: qa-z init --profile {detection.profile}")


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
        project["profile"] = profile
        if profile == "python":
            project["languages"] = ["python"]
        elif profile in {"typescript", "nextjs"}:
            project["languages"] = ["typescript"]
        elif profile in {"monorepo", "mixed"}:
            project["languages"] = ["python", "typescript"]

    fast = config.setdefault("fast", {})
    if isinstance(fast, dict):
        checks = fast.get("checks")
        if profile == "python":
            fast["checks"] = filter_check_items(checks, "py_")
        elif profile in {"typescript", "nextjs"}:
            fast["checks"] = filter_check_items(checks, "ts_")
        elif profile in {"monorepo", "mixed"}:
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
    init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show the files init would write without changing the repository",
    )
    init_parser.add_argument(
        "--explain",
        action="store_true",
        help="print profile detection evidence and starter check assumptions",
    )
    init_parser.set_defaults(handler=handle_init)
