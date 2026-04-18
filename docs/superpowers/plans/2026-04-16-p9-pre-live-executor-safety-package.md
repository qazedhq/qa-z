# P9 Pre-Live Executor Safety Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze QA-Z's pre-live executor safety boundary as one explicit local package shared by repair sessions, executor bridges, and docs.

**Architecture:** Add a small `executor_safety` module that emits one JSON contract plus one Markdown companion. Repair-session start writes the package into the session directory and stores manifest pointers. Executor bridges copy and summarize the same package. Docs and schema references move to that explicit artifact instead of scattered policy text.

**Tech Stack:** Python, pytest, JSON artifacts, Markdown docs.

---

### Task 1: Lock The New Safety Package With Tests

**Files:**
- Modify: `tests/test_repair_session.py`
- Modify: `tests/test_executor_bridge.py`
- Modify: `tests/test_artifact_schema.py`

- [ ] Add a failing repair-session test that requires `executor_safety.json` and `executor_safety.md` to be written at session start.
- [ ] Add a failing bridge test that requires copied safety inputs plus a machine-readable `safety_package` summary in `bridge.json`.
- [ ] Add a failing schema test that requires `safety_artifacts` on repair-session manifests and the stable safety package shape.

### Task 2: Implement The Shared Safety Package

**Files:**
- Create: `src/qa_z/executor_safety.py`

- [ ] Define a stable `qa_z.executor_safety` payload with package id, status, summary, rules, and enforcement points.
- [ ] Add a Markdown renderer for the same package.
- [ ] Add a helper that writes both artifacts deterministically to a target directory.

### Task 3: Attach The Package To Repair Sessions And Bridges

**Files:**
- Modify: `src/qa_z/repair_session.py`
- Modify: `src/qa_z/executor_bridge.py`

- [ ] Write session-local safety artifacts during `repair-session start`.
- [ ] Store session manifest pointers in a new `safety_artifacts` field.
- [ ] Copy the safety artifacts into bridge `inputs/`.
- [ ] Add a bridge `safety_package` summary and mention the package explicitly in session and bridge guides.

### Task 4: Sync Current-Truth Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/repair-sessions.md`
- Modify: `docs/mvp-issues.md`
- Create: `docs/pre-live-executor-safety.md`

- [ ] Document the explicit safety package and its rule set without claiming live executor support.
- [ ] Update repair-session and bridge docs to point to the same package.
- [ ] Update roadmap/current-truth text so P9 is described as a frozen pre-live boundary, not live execution work.

### Task 5: Validate

**Commands:**
- [ ] `python -m pytest tests/test_repair_session.py tests/test_executor_bridge.py tests/test_artifact_schema.py -q`
- [ ] `python -m ruff format --check .`
- [ ] `python -m ruff check .`
- [ ] `python -m mypy src tests`
- [ ] `python -m pytest`
- [ ] `python -m qa_z benchmark --json`
