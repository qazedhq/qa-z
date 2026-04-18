# Executor Safety Rule Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Export the executor safety package's ordered six-rule id catalog and use it as the safety portion of the dry-run rule catalog.

**Architecture:** Add `EXECUTOR_SAFETY_RULE_IDS` in `src/qa_z/executor_safety.py`. Import it in `src/qa_z/executor_dry_run_logic.py` so `DRY_RUN_RULE_IDS` is composed from one dry-run-only id plus the exported safety catalog. Tests lock both package emission order and dry-run composition.

**Tech Stack:** Python, pytest, QA-Z executor safety artifacts, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_safety.py`
- Modify: `src/qa_z/executor_dry_run_logic.py`
- Modify: `tests/test_artifact_schema.py`
- Modify: `tests/test_executor_dry_run_logic.py`
- Modify: `tests/test_current_truth.py`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/artifact-schema-v1.md`

## Task 1: Add RED Tests For Safety Rule Catalog

- [ ] **Step 1: Import the wished-for constant**

In `tests/test_artifact_schema.py`, change:

```python
from qa_z.executor_safety import executor_safety_package
```

to:

```python
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS, executor_safety_package
```

- [ ] **Step 2: Assert safety package ids match the catalog**

Inside `test_executor_safety_package_schema_v1_required_fields_are_stable`, add:

```python
    assert tuple(rule["id"] for rule in payload["rules"]) == EXECUTOR_SAFETY_RULE_IDS
```

- [ ] **Step 3: Update dry-run logic test imports**

In `tests/test_executor_dry_run_logic.py`, add:

```python
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS, executor_safety_package
```

and update `test_dry_run_rule_catalog_extends_executor_safety_package_rules`:

```python
    assert safety_rule_ids == EXECUTOR_SAFETY_RULE_IDS
    assert DRY_RUN_RULE_IDS == DRY_RUN_ONLY_RULE_IDS + EXECUTOR_SAFETY_RULE_IDS
```

- [ ] **Step 4: Confirm RED**

Run:

```bash
python -m pytest tests/test_artifact_schema.py tests/test_executor_dry_run_logic.py -k "executor_safety_package_schema_v1_required_fields_are_stable or extends_executor_safety_package_rules" -q
```

Expected: fail because `EXECUTOR_SAFETY_RULE_IDS` is not exported yet.

## Task 2: Export And Use The Catalog

- [ ] **Step 1: Add the safety rule id tuple**

In `src/qa_z/executor_safety.py`, add after `EXECUTOR_SAFETY_PACKAGE_ID`:

```python
EXECUTOR_SAFETY_RULE_IDS = (
    "no_op_requires_explanation",
    "retry_boundary_is_manual",
    "mutation_scope_limited",
    "unrelated_refactors_prohibited",
    "verification_required_for_completed",
    "outcome_classification_must_be_honest",
)
```

- [ ] **Step 2: Use it from dry-run logic**

In `src/qa_z/executor_dry_run_logic.py`, add:

```python
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS
```

and change `DRY_RUN_RULE_IDS` to:

```python
DRY_RUN_RULE_IDS = DRY_RUN_ONLY_RULE_IDS + EXECUTOR_SAFETY_RULE_IDS
```

- [ ] **Step 3: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_artifact_schema.py tests/test_executor_dry_run_logic.py -k "executor_safety_package_schema_v1_required_fields_are_stable or extends_executor_safety_package_rules or dry_run_rule_catalog" -q
```

Expected: pass.

## Task 3: Current-Truth Docs

- [ ] **Step 1: Add docs guard**

In `tests/test_current_truth.py`, add:

```python
    assert "executor safety rule catalog" in benchmarking
    assert "executor safety rule catalog" in schema
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention the exported safety catalog.

- [ ] **Step 3: Update docs**

Update:

- `README.md`
- `docs/benchmarking.md`
- `docs/artifact-schema-v1.md`

Required phrase:

```text
executor safety rule catalog
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
python -m pytest tests/test_artifact_schema.py tests/test_executor_dry_run_logic.py tests/test_current_truth.py -q
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
