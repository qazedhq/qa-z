# Executor Bridge Safety Rule Count Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic `rule_count` to executor bridge `safety_package` summaries so copied safety package completeness is visible without recounting ids.

**Architecture:** Keep bridge inputs and safety artifacts unchanged. Add one additive manifest field computed from the existing `rule_ids` list, and pin it with bridge plus current-truth tests.

**Tech Stack:** Python, pytest, QA-Z executor bridge manifests, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_bridge.py`
- Modify: `tests/test_executor_bridge.py`
- Modify: `tests/test_current_truth.py`
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`

## Task 1: Add RED Bridge Test

- [ ] **Step 1: Import the safety rule catalog**

In `tests/test_executor_bridge.py`, add:

```python
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS
```

- [ ] **Step 2: Strengthen safety package assertions**

In `test_create_executor_bridge_from_autonomy_loop_packages_inputs`, replace the
loose membership assertion:

```python
    assert "mutation_scope_limited" in manifest["safety_package"]["rule_ids"]
```

with:

```python
    assert manifest["safety_package"]["rule_ids"] == list(EXECUTOR_SAFETY_RULE_IDS)
    assert manifest["safety_package"]["rule_count"] == len(EXECUTOR_SAFETY_RULE_IDS)
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_bridge.py -k "packages_inputs" -q
```

Expected: fail because `safety_package.rule_count` is missing.

## Task 2: Add `rule_count`

- [ ] **Step 1: Update bridge safety summary**

In `src/qa_z/executor_bridge.py`, update `bridge_safety_package_summary()`:

```python
        "rule_ids": rule_ids,
        "rule_count": len(rule_ids),
```

- [ ] **Step 2: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_executor_bridge.py -k "packages_inputs" -q
```

Expected: pass.

## Task 3: Current-Truth Docs

- [ ] **Step 1: Add docs guard**

In `tests/test_current_truth.py`, add:

```python
    assert "safety rule count" in readme
    assert "safety rule count" in schema
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention the new manifest field.

- [ ] **Step 3: Update docs**

Update:

- `README.md`
- `docs/artifact-schema-v1.md`

Required phrase:

```text
safety rule count
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
python -m pytest tests/test_executor_bridge.py tests/test_current_truth.py -q
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
