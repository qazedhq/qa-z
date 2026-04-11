"""Static bootstrap content and config helpers for QA-Z."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml

EXAMPLE_CONFIG = (
    dedent(
        """
    project:
      name: qa-z
      languages:
        - python
      roots:
        - src
        - tests

    contracts:
      sources:
        - issue
        - pull_request
        - spec
        - diff
      output_dir: qa/contracts

    fast:
      default_contract: latest
      output_dir: .qa-z/runs
      strict_no_tests: false
      fail_on_missing_tool: true
      checks:
        - id: py_lint
          enabled: true
          run: ["ruff", "check", "."]
          kind: lint

        - id: py_format
          enabled: true
          run: ["ruff", "format", "--check", "."]
          kind: format

        - id: py_type
          enabled: true
          run: ["mypy", "src", "tests"]
          kind: typecheck

        - id: py_test
          enabled: true
          run: ["pytest", "-q"]
          kind: test
          no_tests: warn

    checks:
      deep:
        - property
        - mutation
        - security
        - e2e_smoke

    gates:
      require_human_review: true
      block_on:
        - failed_unit
        - failed_security
        - missing_contract

    reporters:
      markdown: true
      json: true
      sarif: false
      github_annotations: false
      repair_packet: false

    adapters:
      codex:
        enabled: true
        instructions_file: AGENTS.md
      claude:
        enabled: true
        instructions_file: CLAUDE.md
    """
    ).strip()
    + "\n"
)

CONTRACTS_README = (
    dedent(
        """
    # QA Contracts

    Generated and curated QA contracts live here.

    Each contract should explain:

    - scope
    - assumptions
    - invariants
    - negative cases
    - acceptance checks

    QA-Z will eventually generate and update these files from issue, spec, and diff context.
    """
    ).strip()
    + "\n"
)

COMMAND_GUIDANCE = {
    "fast": dedent(
        """
        qa-z fast runs deterministic Python checks.

        Current responsibility:
        - run configured subprocess checks without LLM judgment
        - normalize pass, fail, warning, skipped, and tool errors
        - emit JSON and Markdown artifacts under .qa-z/runs
        """
    ).strip(),
    "deep": dedent(
        """
        qa-z deep is scaffolded, not fully implemented yet.

        Planned responsibility:
        - run property, mutation, security, and smoke E2E checks
        - gate critical-path changes with stronger evidence
        - surface higher-cost failures with repair guidance
        """
    ).strip(),
    "review": dedent(
        """
        qa-z review is scaffolded, not fully implemented yet.

        Planned responsibility:
        - compress runner results into a PR review packet
        - emit human-readable findings plus machine-readable annotations
        - keep pass/fail tied to deterministic checks
        """
    ).strip(),
    "repair-prompt": dedent(
        """
        qa-z repair-prompt is scaffolded, not fully implemented yet.

        Planned responsibility:
        - convert failures into an agent-friendly repair packet
        - highlight broken contracts, affected files, and next questions
        - make the next agent loop easier instead of noisier
        """
    ).strip(),
}


def load_config(root: Path, config_path: Path | None = None) -> dict[str, Any]:
    """Load qa-z configuration or fall back to the built-in example config."""
    target = config_path if config_path is not None else root / "qa-z.yaml"

    if target.exists():
        raw = target.read_text(encoding="utf-8")
    else:
        raw = EXAMPLE_CONFIG

    loaded = yaml.safe_load(raw) or {}
    if not isinstance(loaded, dict):
        raise ValueError("QA-Z config must deserialize into a mapping.")
    return loaded


def get_nested(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely fetch nested config values."""
    current: Any = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
