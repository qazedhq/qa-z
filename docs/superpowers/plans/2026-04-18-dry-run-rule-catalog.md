# Dry-Run Rule Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Export the executor dry-run rule id catalog from production logic and make tests/docs use it as the source of truth.

**Architecture:** Add a `DRY_RUN_RULE_IDS` tuple beside `evaluate_rules()` in `src/qa_z/executor_dry_run_logic.py`. Logic tests verify the tuple matches emitted rule order; benchmark corpus tests compare fixture bucket unions against the tuple instead of a copied literal.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_dry_run_logic.py`
- Modify: `tests/test_executor_dry_run_logic.py`
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/artifact-schema-v1.md`

## Task 1: Add RED Tests For The Catalog

- [ ] **Step 1: Import the wished-for catalog**

In `tests/test_executor_dry_run_logic.py`, change the import to:

```python
from qa_z.executor_dry_run_logic import (
    DRY_RUN_RULE_IDS,
    build_dry_run_summary,
    evaluate_rules,
)
```

- [ ] **Step 2: Add the catalog order test**

Add:

```python
def test_dry_run_rule_catalog_matches_evaluated_rule_order() -> None:
    assert tuple(item["id"] for item in evaluate_rules([], {})) == DRY_RUN_RULE_IDS
```

- [ ] **Step 3: Update benchmark test import**

In `tests/test_benchmark.py`, import `DRY_RUN_RULE_IDS` from
`qa_z.executor_dry_run_logic`.

- [ ] **Step 4: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py tests/test_benchmark.py -k "dry_run_rule_catalog or complete_rule_buckets" -q
```

Expected: fail because `DRY_RUN_RULE_IDS` is not exported yet.

## Task 2: Export The Catalog And Remove Test Duplication

- [ ] **Step 1: Add the tuple**

In `src/qa_z/executor_dry_run_logic.py`, add:

```python
DRY_RUN_RULE_IDS = (
    "executor_history_recorded",
    "no_op_requires_explanation",
    "retry_boundary_is_manual",
    "mutation_scope_limited",
    "unrelated_refactors_prohibited",
    "verification_required_for_completed",
    "outcome_classification_must_be_honest",
)
```

- [ ] **Step 2: Update benchmark completeness test**

Replace the hard-coded `expected_rule_ids` set with:

```python
    expected_rule_ids = set(DRY_RUN_RULE_IDS)
```

- [ ] **Step 3: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py tests/test_benchmark.py -k "dry_run_rule_catalog or complete_rule_buckets" -q
```

Expected: pass.

## Task 3: Current-Truth Docs

- [ ] **Step 1: Add current-truth assertion**

In `tests/test_current_truth.py`, assert:

```python
    assert "dry-run rule catalog" in benchmarking
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention the catalog distinction.

- [ ] **Step 3: Update docs**

Mention that the dry-run rule catalog is the seven-rule runtime audit set in:

- `README.md`
- `docs/benchmarking.md`
- `docs/artifact-schema-v1.md`

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
python -m pytest tests/test_executor_dry_run_logic.py tests/test_benchmark.py tests/test_current_truth.py -q
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
