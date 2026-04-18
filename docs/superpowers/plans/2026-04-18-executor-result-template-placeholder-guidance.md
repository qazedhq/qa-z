# Executor Result Template Placeholder Guidance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make bridge guides and non-JSON stdout explicitly tell operators to replace the executor result template's placeholder summary before ingest or re-entry.

**Architecture:** Reuse the existing `PLACEHOLDER_SUMMARY` constant from `qa_z.executor_result`. Add renderer-only guidance in `executor_bridge.py`; keep result template schema, ingest validation, and JSON manifest output unchanged.

**Tech Stack:** Python, pytest, QA-Z executor bridge renderers, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_bridge.py`
- Modify: `tests/test_executor_bridge.py`
- Modify: `tests/test_current_truth.py`
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`

## Task 1: Add RED Guide Assertions

- [ ] **Step 1: Import placeholder constant in the test**

In `tests/test_executor_bridge.py`, add:

```python
from qa_z.executor_result import PLACEHOLDER_SUMMARY
```

- [ ] **Step 2: Assert guide files mention placeholder replacement**

In `test_executor_bridge_from_loop_packages_manifest_guides_and_inputs`, add:

```python
    placeholder_guidance = (
        "Replace the placeholder summary before ingest: "
        f"`{PLACEHOLDER_SUMMARY}`"
    )
    assert placeholder_guidance in guide
    assert placeholder_guidance in codex
    assert placeholder_guidance in claude
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_bridge.py -k "from_loop_packages_manifest_guides_and_inputs" -q
```

Expected: fail because the bridge guides do not mention placeholder summary
replacement.

## Task 2: Add RED Stdout Assertion

- [ ] **Step 1: Assert stdout mentions placeholder replacement**

In `test_executor_bridge_cli_stdout_points_to_return_and_safety_entrypoints`,
add:

```python
    assert "Template summary: replace placeholder before ingest" in output
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_bridge.py -k "stdout_points_to_return_and_safety_entrypoints" -q
```

Expected: fail because stdout does not mention placeholder summary replacement.

## Task 3: Render Placeholder Guidance

- [ ] **Step 1: Import the placeholder constant**

In `src/qa_z/executor_bridge.py`, change:

```python
from qa_z.executor_result import executor_result_template
```

to:

```python
from qa_z.executor_result import PLACEHOLDER_SUMMARY, executor_result_template
```

- [ ] **Step 2: Add a helper**

Add:

```python
def bridge_placeholder_summary_guidance() -> str:
    """Return stable guidance for completing result templates."""
    return (
        "Replace the placeholder summary before ingest: "
        f"`{PLACEHOLDER_SUMMARY}`"
    )
```

- [ ] **Step 3: Render it in bridge guides**

In `render_executor_bridge_guide()` and `render_executor_specific_guide()`,
append:

```python
            f"- {bridge_placeholder_summary_guidance()}",
```

inside each Return Contract section.

- [ ] **Step 4: Render it in stdout**

In `render_bridge_stdout()`, add:

```python
        "Template summary: replace placeholder before ingest",
```

- [ ] **Step 5: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_executor_bridge.py -k "from_loop_packages_manifest_guides_and_inputs or stdout_points_to_return_and_safety_entrypoints" -q
```

Expected: pass.

## Task 4: Current-Truth Documentation

- [ ] **Step 1: Add docs guard**

In `tests/test_current_truth.py`, add:

```python
    assert "template placeholder guidance" in readme
    assert "template placeholder guidance" in schema
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until README and schema mention the new guidance.

- [ ] **Step 3: Update docs**

Update:

- `README.md`
- `docs/artifact-schema-v1.md`

Required phrase:

```text
template placeholder guidance
```

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 5: Verification

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
