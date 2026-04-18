# Dry-Run Safety Catalog Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the dry-run rule catalog is exactly the frozen executor safety package rule set plus the dry-run-only history audit rule.

**Architecture:** Add `DRY_RUN_ONLY_RULE_IDS` beside `DRY_RUN_RULE_IDS`. Add a focused unit test that compares the dry-run catalog to `executor_safety_package()["rules"]` without changing runtime dry-run evaluation.

**Tech Stack:** Python, pytest, QA-Z executor safety artifacts, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_dry_run_logic.py`
- Modify: `tests/test_executor_dry_run_logic.py`
- Modify: `tests/test_current_truth.py`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/artifact-schema-v1.md`

## Task 1: Add RED Catalog Alignment Test

- [ ] **Step 1: Import the wished-for constant and safety package**

In `tests/test_executor_dry_run_logic.py`, update imports:

```python
from qa_z.executor_dry_run_logic import (
    DRY_RUN_ONLY_RULE_IDS,
    DRY_RUN_RULE_IDS,
    build_dry_run_summary,
    evaluate_rules,
)
from qa_z.executor_safety import executor_safety_package
```

- [ ] **Step 2: Add the alignment test**

Add:

```python
def test_dry_run_rule_catalog_extends_executor_safety_package_rules() -> None:
    safety_rule_ids = tuple(
        rule["id"] for rule in executor_safety_package()["rules"]
    )

    assert DRY_RUN_ONLY_RULE_IDS == ("executor_history_recorded",)
    assert DRY_RUN_RULE_IDS == DRY_RUN_ONLY_RULE_IDS + safety_rule_ids
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -k "extends_executor_safety_package_rules" -q
```

Expected: fail because `DRY_RUN_ONLY_RULE_IDS` does not exist yet.

## Task 2: Add The Dry-Run-Only Rule Constant

- [ ] **Step 1: Add the constant**

In `src/qa_z/executor_dry_run_logic.py`, add above `DRY_RUN_RULE_IDS`:

```python
DRY_RUN_ONLY_RULE_IDS = ("executor_history_recorded",)
```

- [ ] **Step 2: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py -k "extends_executor_safety_package_rules or dry_run_rule_catalog" -q
```

Expected: pass.

## Task 3: Current-Truth Docs

- [ ] **Step 1: Add current-truth assertion**

In `tests/test_current_truth.py`, add:

```python
    assert "extends the frozen safety package" in benchmarking
    assert "extends the frozen safety package" in schema
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs include the phrase.

- [ ] **Step 3: Update docs**

Update:

- `README.md`
- `docs/benchmarking.md`
- `docs/artifact-schema-v1.md`

Required phrase:

```text
extends the frozen safety package
```

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 4: Verification

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py tests/test_current_truth.py -q
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
