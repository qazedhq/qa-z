# Pre-Live Safety Catalog Doc Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep `docs/pre-live-executor-safety.md` synchronized with the current executor safety catalog, dry-run catalog extension, and bridge safety rule count language.

**Architecture:** Add current-truth tests that pin the pre-live safety document to the same catalog terminology already present in README, benchmarking, and schema docs. Then update only the Markdown document.

**Tech Stack:** pytest, Markdown docs.

---

## Files

- Modify: `tests/test_current_truth.py`
- Modify: `docs/pre-live-executor-safety.md`

## Task 1: Add RED Current-Truth Guard

- [ ] **Step 1: Read the pre-live safety doc**

In `tests/test_current_truth.py`, inside
`test_executor_dry_run_retry_noop_benchmark_density_is_documented`, add:

```python
    pre_live_safety = (ROOT / "docs" / "pre-live-executor-safety.md").read_text(
        encoding="utf-8"
    )
```

- [ ] **Step 2: Assert catalog language is present**

Add:

```python
    assert "executor safety rule catalog" in pre_live_safety
    assert "six-rule frozen pre-live set" in pre_live_safety
    assert "safety rule count" in pre_live_safety
    assert "dry-run rule catalog" in pre_live_safety
    assert "executor_history_recorded" in pre_live_safety
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail because `docs/pre-live-executor-safety.md` does not yet mention
the catalog/count relationship.

## Task 2: Update Pre-Live Safety Docs

- [ ] **Step 1: Update the package section**

Add language that the JSON package is the machine-readable source of truth for
the executor safety rule catalog and bridge surfaces expose a safety rule count.

- [ ] **Step 2: Update the frozen rules section**

State that the current catalog is the six-rule frozen pre-live set.

- [ ] **Step 3: Update the dry-run section**

Clarify that the dry-run rule catalog extends the frozen package with
`executor_history_recorded` for history-presence auditing.

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 3: Verification

- [ ] **Step 1: Run full tests**

Run:

```bash
python -m pytest
```

Expected: all tests pass except the existing skipped test.

- [ ] **Step 2: Run full benchmark**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: every committed benchmark fixture passes.

## VCS Note

Do not stage or commit in this pass. The active workspace already contains many
unrelated local changes.
