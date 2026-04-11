# QA-Z Fast Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `qa-z fast` as a deterministic Python-first merge gate that runs configured checks and writes JSON plus Markdown artifacts.

**Architecture:** The CLI will load config and an optional contract, then delegate orchestration to focused runner modules. The runner treats checks as explicit subprocess specs, normalizes results into dataclasses, writes stable artifacts, and returns documented exit codes without invoking LLMs or auto-fixes.

**Tech Stack:** Python 3.10+, argparse, pathlib, subprocess, dataclasses, json, pytest, PyYAML

---

### Task 1: Lock CLI Behavior With Failing Tests

**Files:**
- Modify: `tests/test_cli.py`

- [ ] Add tests for `qa-z fast --json`, artifact creation, explicit contract selection, missing-tool exit code, unsupported-check exit code, and strict no-tests behavior.
- [ ] Run `python -m pytest tests/test_cli.py -q` and confirm the new tests fail because `fast` is still a placeholder.

### Task 2: Add Runner Models And Subprocess Execution

**Files:**
- Create: `src/qa_z/runners/models.py`
- Create: `src/qa_z/runners/subprocess.py`

- [ ] Add `CheckSpec`, `CheckResult`, and `RunSummary` dataclasses with JSON-safe serialization.
- [ ] Add a subprocess executor that captures stdout/stderr tails, duration, exit code, and missing executable errors.
- [ ] Run the focused tests and confirm the model/executor expectations pass while CLI wiring still fails.

### Task 3: Build Python Fast Orchestration

**Files:**
- Create: `src/qa_z/runners/python.py`
- Create: `src/qa_z/runners/fast.py`

- [ ] Resolve top-level `fast.checks` config first, then fall back to the bootstrap `checks.fast` list.
- [ ] Provide Python defaults for `py_lint`, `py_format`, `py_type`, and `py_test`.
- [ ] Normalize pytest exit code 5 with the configured `no_tests` or `strict_no_tests` policy.
- [ ] Return exit code `0`, `1`, `2`, `3`, or `4` according to the documented fast-runner contract.

### Task 4: Add Summary Reporters

**Files:**
- Create: `src/qa_z/reporters/run_summary.py`

- [ ] Write `.qa-z/runs/<timestamp>/fast/summary.json`.
- [ ] Write `.qa-z/runs/<timestamp>/fast/summary.md`.
- [ ] Write one JSON file per check under `checks/`.

### Task 5: Wire CLI And Docs

**Files:**
- Modify: `src/qa_z/cli.py`
- Modify: `src/qa_z/config.py`
- Modify: `src/qa_z/planner/contracts.py`
- Modify: `README.md`
- Modify: `qa-z.yaml.example`
- Modify: `docs/mvp-issues.md`

- [ ] Replace the `fast` placeholder with `--contract`, `--output-dir`, `--json`, and `--strict-no-tests`.
- [ ] Keep `deep` and `repair-prompt` scaffolded.
- [ ] Update public docs to say `fast` is a Python deterministic runner, not deep QA automation.
- [ ] Run `python -m pytest`.
