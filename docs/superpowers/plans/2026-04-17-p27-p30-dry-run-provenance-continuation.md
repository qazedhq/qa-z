# P27-P30 Dry-Run Provenance Continuation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve dry-run history residue provenance across repair-session, publish, and GitHub summary surfaces even when materialized session summaries are missing.

**Architecture:** Keep the existing dry-run summary contract, add one additive provenance field, reuse history-only synthesis in publish fallback paths, and lock the behavior with focused regression tests before broad validation.

**Tech Stack:** Python, pytest, Markdown docs

---

### Task 1: Expand failing provenance tests

- [ ] Assert repair-session summary and status JSON distinguish `materialized` vs `history_fallback`
- [ ] Assert publish summaries keep dry-run provenance when session `summary.json` exists
- [ ] Assert publish summaries still recover dry-run residue when `summary.json` is missing but verify artifacts and history remain
- [ ] Assert GitHub summary renders the same fallback provenance and dry-run fields

### Task 2: Implement publish/github provenance carry-through

- [ ] Add an additive `executor_dry_run_source` field to session publish surfaces
- [ ] Load dry-run residue before session-summary fallback so verify-artifact fallback can still include it
- [ ] Render provenance compactly without changing existing verification recommendations

### Task 3: Tighten dry-run fallback realism coverage

- [ ] Add at least one extra history-only edge-case test for blocked fallback caused by scope or verification conflicts
- [ ] Keep all new assertions deterministic and artifact-driven

### Task 4: Update docs and milestone tracking

- [ ] Document `executor_dry_run_source` in artifact schema docs
- [ ] Record the new fallback behavior in `docs/mvp-issues.md`

### Task 5: Validate the repo

- [ ] Run focused pytest coverage for repair-session, publish, and GitHub summary paths
- [ ] Run `python -m ruff format --check .`
- [ ] Run `python -m ruff check .`
- [ ] Run `python -m mypy src tests`
- [ ] Run `python -m pytest`
- [ ] Run `python -m qa_z benchmark --json`
