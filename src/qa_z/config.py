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
        - typescript
      roots:
        - src
        - tests
      critical_paths:
        - auth/**
        - payments/**
        - migrations/**

    contracts:
      sources:
        - issue
        - pull_request
        - spec
        - diff
      output_dir: qa/contracts
      required_sections:
        - scope
        - assumptions
        - invariants
        - risk_edges
        - negative_cases
        - acceptance_checks

    fast:
      default_contract: latest
      output_dir: ".qa-z/runs"
      strict_no_tests: false
      fail_on_missing_tool: true
      selection:
        default_mode: "full"
        full_run_threshold: 40
        high_risk_paths:
          - package.json
          - package-lock.json
          - pnpm-lock.yaml
          - yarn.lock
          - tsconfig.json
          - tsconfig.base.json
          - vitest.config.ts
          - vitest.config.js
          - vite.config.ts
          - vite.config.js
          - eslint.config.js
          - eslint.config.mjs
          - .eslintrc.json

      checks:
        - id: py_lint
          enabled: true
          run: ["ruff", "check", "."]
          kind: "lint"

        - id: py_format
          enabled: true
          run: ["ruff", "format", "--check", "."]
          kind: "format"

        - id: py_type
          enabled: true
          run: ["mypy", "src", "tests"]
          kind: "typecheck"

        - id: py_test
          enabled: true
          run: ["pytest", "-q"]
          kind: "test"
          no_tests: "warn"

        - id: ts_lint
          enabled: true
          run: ["eslint", "."]
          kind: "lint"

        - id: ts_type
          enabled: true
          run: ["tsc", "--noEmit"]
          kind: "typecheck"

        - id: ts_test
          enabled: true
          run: ["vitest", "run"]
          kind: "test"
          no_tests: "warn"

    deep:
      fail_on_missing_tool: true
      selection:
        default_mode: "full"
        full_run_threshold: 15
        exclude_paths:
          - dist/**
          - build/**
          - coverage/**
          - "**/*.generated.*"
        high_risk_paths:
          - qa-z.yaml
          - pyproject.toml
          - package.json
          - tsconfig.json
          - eslint.config.js
      checks:
        - id: sg_scan
          enabled: true
          run: ["semgrep", "--json"]
          kind: "static-analysis"
          semgrep:
            config: "auto"
            fail_on_severity:
              - ERROR
            ignore_rules: []

    checks:
      selection:
        mode: diff-aware
        max_changed_files: 40

    gates:
      require_human_review: true
      escalate_on:
        - auth/**
        - billing/**
        - infra/**
      block_on:
        - failed_unit
        - failed_security
        - missing_contract

    reporters:
      markdown: true
      json: true
      sarif: true
      github_annotations: false
      repair_packet: true

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
        qa-z fast runs deterministic Python and TypeScript checks.

        Current responsibility:
        - run configured subprocess checks without LLM judgment
        - target eligible Python and TypeScript checks from changed-file metadata
        - normalize pass, fail, warning, skipped, and tool errors
        - emit JSON and Markdown artifacts under .qa-z/runs
        """
    ).strip(),
    "deep": dedent(
        """
        qa-z deep runs configured higher-cost checks.

        Current responsibility:
        - run configured Semgrep checks through sg_scan
        - skip docs-only smart selections and target source/test changes
        - normalize Semgrep JSON findings into summary artifacts
        - apply Semgrep severity thresholds, config overrides, grouping, and suppression
        - emit SARIF 2.1.0 for normalized deep findings
        - preserve summary and check artifacts when Semgrep fails

        Planned responsibility:
        - add property, mutation, and smoke E2E checks
        - gate critical-path changes with stronger evidence
        - surface higher-cost failures with repair guidance
        """
    ).strip(),
    "review": dedent(
        """
        qa-z review renders a deterministic review packet from local artifacts.

        Current responsibility:
        - render review packets from a contract or attached run artifacts
        - include fast-check context and sibling deep findings when available
        - emit human-readable Markdown plus machine-readable JSON
        """
    ).strip(),
    "repair-prompt": dedent(
        """
        qa-z repair-prompt builds a deterministic repair packet from local artifacts.

        Current responsibility:
        - convert failed fast checks and blocking deep findings into repair artifacts
        - highlight affected files, validation commands, and next repair targets
        - emit human-readable Markdown plus machine-readable JSON
        """
    ).strip(),
}


class ConfigError(ValueError):
    """Raised when qa-z configuration cannot be loaded."""


def load_config(root: Path, config_path: Path | None = None) -> dict[str, Any]:
    """Load qa-z configuration or fall back to the built-in example config."""
    target = config_path if config_path is not None else root / "qa-z.yaml"

    if target.exists():
        raw = target.read_text(encoding="utf-8")
    else:
        raw = EXAMPLE_CONFIG

    try:
        loaded = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Could not parse {target}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ConfigError("QA-Z config must deserialize into a mapping.")
    return loaded


def get_nested(config: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely fetch nested config values."""
    current: Any = config
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current
