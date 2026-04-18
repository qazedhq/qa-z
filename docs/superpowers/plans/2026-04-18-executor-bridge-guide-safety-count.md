# Executor Bridge Guide Safety Count Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the copied safety package rule count in every executor-facing bridge guide so operators can audit package completeness without opening `bridge.json`.

**Architecture:** Keep `bridge.json` as the source of truth. Add a small renderer helper that reads `safety_package.rule_count` with a defensive fallback to `len(rule_ids)`, then render the count in `executor_guide.md`, `codex.md`, and `claude.md`.

**Tech Stack:** Python, pytest, QA-Z executor bridge renderers, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_bridge.py`
- Modify: `tests/test_executor_bridge.py`
- Modify: `tests/test_current_truth.py`
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`

## Task 1: Add RED Bridge Guide Assertions

- [ ] **Step 1: Pin the expected display text**

In `tests/test_executor_bridge.py`, inside
`test_executor_bridge_from_loop_packages_manifest_guides_and_inputs`, add:

```python
    expected_rule_count = len(EXECUTOR_SAFETY_RULE_IDS)
```

near the existing safety package assertions.

- [ ] **Step 2: Assert every guide renders the rule count**

Add these assertions after the guide, Codex, and Claude text assertions:

```python
    assert f"Safety rule count: `{expected_rule_count}`" in guide
    assert f"Safety rule count: `{expected_rule_count}`" in codex
    assert f"Safety rule count: `{expected_rule_count}`" in claude
```

- [ ] **Step 3: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_bridge.py -k "from_loop_packages_manifest_guides_and_inputs" -q
```

Expected: fail because the guide renderers do not yet print the safety rule
count.

## Task 2: Render The Safety Rule Count

- [ ] **Step 1: Add a renderer helper**

In `src/qa_z/executor_bridge.py`, add:

```python
def bridge_safety_rule_count(manifest: dict[str, Any]) -> int | str:
    """Return the displayable safety rule count for bridge guides."""
    safety_package = manifest.get("safety_package")
    if not isinstance(safety_package, dict):
        return "unknown"
    rule_count = safety_package.get("rule_count")
    if isinstance(rule_count, int):
        return rule_count
    rule_ids = safety_package.get("rule_ids")
    if isinstance(rule_ids, list):
        return len(rule_ids)
    return "unknown"
```

- [ ] **Step 2: Render the count in `executor_guide.md`**

In `render_executor_bridge_guide()`, after the policy Markdown line, add:

```python
    lines.append(
        f"- Safety rule count: `{bridge_safety_rule_count(manifest)}`"
    )
```

- [ ] **Step 3: Render the count in Codex and Claude wrappers**

In `render_executor_specific_guide()`, after the safety package path line, add:

```python
        f"- Safety rule count: `{bridge_safety_rule_count(manifest)}`",
```

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_executor_bridge.py -k "from_loop_packages_manifest_guides_and_inputs" -q
```

Expected: pass.

## Task 3: Current-Truth Documentation

- [ ] **Step 1: Add docs guard**

In `tests/test_current_truth.py`, add:

```python
    assert "guide safety rule count" in readme
    assert "guide safety rule count" in schema
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until docs mention the guide safety rule count.

- [ ] **Step 3: Update docs**

Update:

- `README.md`
- `docs/artifact-schema-v1.md`

Required phrase:

```text
guide safety rule count
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
