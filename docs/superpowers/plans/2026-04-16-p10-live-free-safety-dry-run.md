# P10 Live-Free Safety Dry-Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add session-scoped executor attempt history plus an explicit `executor-result dry-run` command that evaluates that history against the frozen pre-live safety package.

**Architecture:** Keep ingest as the authoritative result classifier, then append a session-local attempt record for every readable result when the session can be resolved. Build the dry-run command as a separate deterministic reader that consumes session history plus the P9 safety package and writes summary/report artifacts without mutating code or rerunning verification.

**Tech Stack:** Python, pytest, JSON artifacts, Markdown reports, argparse CLI.

---

### Task 1: Lock Session Attempt History With Tests

**Files:**
- Modify: `F:/JustTyping/tests/test_executor_result.py`
- Modify: `F:/JustTyping/tests/test_artifact_schema.py`

- [ ] Add a failing ingest test that expects accepted results to append a session-local attempt record under `.qa-z/sessions/<session-id>/executor_results/history.json`.
- [ ] Add a failing ingest test that expects a readable rejected result to still append to session history when the session exists.
- [ ] Add a failing schema test for the new executor-result history artifact shape.
- [ ] Run: `python -m pytest tests/test_executor_result.py tests/test_artifact_schema.py -q`

### Task 2: Implement Session History Storage

**Files:**
- Create: `F:/JustTyping/src/qa_z/executor_history.py`
- Modify: `F:/JustTyping/src/qa_z/executor_result.py`
- Modify: `F:/JustTyping/src/qa_z/executor_ingest.py`
- Modify: `F:/JustTyping/src/qa_z/repair_session.py`

- [ ] Add stable helpers for history paths, empty history payloads, attempt-id allocation, append-only history writes, and compatibility backfill from an older session's latest stored result.
- [ ] Update ingest so finalized accepted outcomes append to history.
- [ ] Update readable rejected ingest paths so they append to history when the session is already available.
- [ ] Keep `executor_result.json` as the latest accepted session artifact for backward compatibility.
- [ ] Add additive session manifest pointers for history path, attempt count, and latest attempt id if that stays narrow and deterministic.
- [ ] Run: `python -m pytest tests/test_executor_result.py tests/test_artifact_schema.py -q`

### Task 3: Lock Dry-Run Behavior With Tests

**Files:**
- Modify: `F:/JustTyping/tests/test_executor_result.py`
- Modify: `F:/JustTyping/tests/test_cli.py`

- [ ] Add a failing dry-run test for a clear single-attempt history.
- [ ] Add a failing dry-run test for repeated partial or rejected attempts producing `attention_required`.
- [ ] Add a failing dry-run test for completed-but-verify-blocked history producing `blocked`.
- [ ] Add a failing CLI test for `qa-z executor-result dry-run --session ... --json`.
- [ ] Run: `python -m pytest tests/test_executor_result.py tests/test_cli.py -q`

### Task 4: Implement The Dry-Run Audit

**Files:**
- Create: `F:/JustTyping/src/qa_z/executor_dry_run.py`
- Modify: `F:/JustTyping/src/qa_z/cli.py`
- Modify: `F:/JustTyping/src/qa_z/executor_safety.py`

- [ ] Implement deterministic loading of session manifest, safety package, and executor-result history.
- [ ] Evaluate history signals and rule-level statuses against the frozen safety rules.
- [ ] Write `dry_run_summary.json` and `dry_run_report.md` under the session executor-results directory.
- [ ] Add the `executor-result dry-run` CLI subcommand and human-readable stdout.
- [ ] Run: `python -m pytest tests/test_executor_result.py tests/test_cli.py -q`

### Task 5: Feed History Back Into Self-Inspection

**Files:**
- Modify: `F:/JustTyping/src/qa_z/self_improvement.py`
- Modify: `F:/JustTyping/tests/test_self_improvement.py`

- [ ] Add failing self-inspection tests for repeated partial, no-op, and rejected attempt patterns.
- [ ] Implement session-history candidate discovery without requiring the explicit dry-run command to have run first.
- [ ] Reuse existing backlog categories where possible, especially `partial_completion_gap`, `no_op_safeguard_gap`, and `workflow_gap`.
- [ ] Run: `python -m pytest tests/test_self_improvement.py -q`

### Task 6: Sync Docs And Schema

**Files:**
- Modify: `F:/JustTyping/README.md`
- Modify: `F:/JustTyping/docs/artifact-schema-v1.md`
- Modify: `F:/JustTyping/docs/repair-sessions.md`
- Modify: `F:/JustTyping/docs/pre-live-executor-safety.md`
- Modify: `F:/JustTyping/docs/mvp-issues.md`
- Modify: `F:/JustTyping/docs/reports/current-state-analysis.md`
- Modify: `F:/JustTyping/docs/reports/next-improvement-roadmap.md`

- [ ] Document the new session-local history area and dry-run command.
- [ ] Explain that dry-run is explicit and live-free.
- [ ] Explain how repeated attempt history now feeds self-improvement.
- [ ] Keep all docs honest about the continued absence of live executor support.

### Task 7: Full Validation

**Files:**
- Verify only

- [ ] Run: `python -m pytest tests/test_executor_result.py tests/test_artifact_schema.py tests/test_cli.py tests/test_self_improvement.py -q`
- [ ] Run: `python -m ruff format --check .`
- [ ] Run: `python -m ruff check .`
- [ ] Run: `python -m mypy src tests`
- [ ] Run: `python -m pytest`
- [ ] Run: `python -m qa_z benchmark --json`
