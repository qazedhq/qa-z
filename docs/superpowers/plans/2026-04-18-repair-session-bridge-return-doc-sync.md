# Repair Session Bridge Return Doc Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep `docs/repair-sessions.md` synchronized with the latest executor-bridge stdout return pointers and result-template placeholder guidance.

**Architecture:** Add current-truth tests that pin the repair-session workflow doc to the same bridge return-path language already present in README and schema docs. Then update only the documentation.

**Tech Stack:** pytest, Markdown docs.

---

## Files

- Modify: `tests/test_current_truth.py`
- Modify: `docs/repair-sessions.md`

## Task 1: Add RED Current-Truth Guard

- [ ] **Step 1: Read repair-session docs in the current-truth test**

In `tests/test_current_truth.py`, inside
`test_executor_dry_run_retry_noop_benchmark_density_is_documented`, add:

```python
    repair_sessions = (ROOT / "docs" / "repair-sessions.md").read_text(
        encoding="utf-8"
    )
```

- [ ] **Step 2: Assert bridge return-path phrases are present**

Add:

```python
    assert "bridge stdout return pointers" in repair_sessions
    assert "template placeholder guidance" in repair_sessions
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail because `docs/repair-sessions.md` does not yet mention those
phrases.

## Task 2: Update Repair Session Docs

- [ ] **Step 1: Extend the Executor Bridge section**

In `docs/repair-sessions.md`, after the paragraph describing `bridge.json`,
`result_template.json`, `executor_guide.md`, `codex.md`, and `claude.md`, add:

```markdown
Human stdout includes bridge stdout return pointers for the result template,
expected result artifact, copied safety package, safety rule count, and
verification command. The bridge guides and stdout also include template
placeholder guidance so the scaffolded result summary is replaced before
`executor-result ingest`.
```

- [ ] **Step 2: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 3: Verification

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

- [ ] **Step 2: Run full tests**

Run:

```bash
python -m pytest
```

Expected: all tests pass except the existing skipped test.

- [ ] **Step 3: Run full benchmark**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: every committed benchmark fixture passes.

## VCS Note

Do not stage or commit in this pass. The active workspace already contains many
unrelated local changes.
