# P6-B Executor Result Ingest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a structured external executor result contract plus an ingest/resume workflow that reconnects bridge output to repair-session verification, loop history, and service-grade self-improvement evidence.

**Architecture:** Keep the contract additive. Extend `executor_bridge` to emit a return template, add a focused `executor_result` module for schema validation and ingest behavior, and keep the CLI thin by wiring a new `executor-result ingest` surface to existing repair-session verification logic. Persist result artifacts under the session directory and enrich loop history only when the new result is grounded in an existing bridge or session.

**Tech Stack:** Python dataclasses, JSON artifacts, argparse CLI, pytest.

---

### Task 1: Lock The Return Contract With Tests

**Files:**
- Modify: `tests/test_executor_bridge.py`
- Modify: `tests/test_artifact_schema.py`
- Modify: `tests/test_cli.py`
- Create: `tests/test_executor_result.py`

- [ ] Add a bridge test that requires a machine-readable executor result template and expected return-contract metadata.
- [ ] Add artifact schema coverage for the new executor result payload and any new repair-session manifest pointers.
- [ ] Add CLI parser coverage for the new `executor-result` command.
- [ ] Add ingest tests that prove status classification, changed-file summaries, session updates, history enrichment, and verification resume behavior.
- [ ] Run the new targeted tests and confirm they fail for the missing feature, not for fixture mistakes.

### Task 2: Implement The Executor Result Contract

**Files:**
- Modify: `src/qa_z/executor_bridge.py`
- Create: `src/qa_z/executor_result.py`

- [ ] Define a stable `qa_z.executor_result` schema with explicit status, validation, changed-file, and verification-hint fields.
- [ ] Emit a bridge-local result template so outside executors know exactly what to return.
- [ ] Extend the bridge return contract with the expected result artifact path and next-step rules for `completed`, `partial`, `failed`, and `no_op`.

### Task 3: Implement Ingest And Resume

**Files:**
- Create: `src/qa_z/executor_result.py`
- Modify: `src/qa_z/repair_session.py`
- Modify: `src/qa_z/autonomy.py`
- Modify: `src/qa_z/cli.py`

- [ ] Validate and ingest executor result JSON from a bridge or session reference.
- [ ] Persist the ingested result under the owning session and update the session manifest with the latest result pointers and status.
- [ ] Derive the next deterministic verification step: use an explicit candidate run when present, otherwise rerun local QA when the result requests rerun validation.
- [ ] Reuse the existing repair-session verification flow when resume conditions are met.
- [ ] Enrich the matching loop history entry with executor result status, changed files, validation summary, and final verification verdict when available.

### Task 4: Documentation Sync

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`

- [ ] Document the new `executor-result ingest` command, bridge result template, and the repaired return-to-verification loop.
- [ ] Update the artifact schema reference with the executor result and session/history enrichment fields.
- [ ] Advance the MVP issue status so the roadmap no longer claims executor result application is entirely missing.

### Task 5: Validation

**Commands:**
- `python -m pytest tests/test_executor_bridge.py tests/test_executor_result.py tests/test_artifact_schema.py tests/test_cli.py`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy src tests`
- `python -m pytest`
- `python -m qa_z benchmark --json`
