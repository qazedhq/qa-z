# Executor Bridge Stdout Benchmark Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Pin executor-bridge human stdout action-context diagnostics in benchmark summaries and committed fixture expectations.

**Architecture:** Extend `summarize_executor_bridge_actual()` to call the existing `render_bridge_stdout(manifest)` renderer and derive additive boolean fields from that text. Existing fixture contracts then compare those fields through the standard `expect_executor_bridge` section.

**Tech Stack:** Python standard library, pytest, existing QA-Z benchmark and executor-bridge helpers.

---

### Task 1: Pin Fixture Expectations

**Files:**
- Modify: `benchmarks/fixtures/executor_bridge_action_context_inputs/expected.json`
- Modify: `benchmarks/fixtures/executor_bridge_missing_action_context_inputs/expected.json`
- Modify: `tests/test_benchmark.py`

- [x] **Step 1: Add stdout expectations to bridge fixtures**

Add `stdout_mentions_action_context: true` to both bridge action-context
fixtures. Add `stdout_mentions_missing_action_context: true` to the missing
context fixture.

- [x] **Step 2: Add corpus assertions**

Extend `test_committed_benchmark_corpus_has_executor_bridge_action_context_fixture`
so it asserts those fixture expectations are present.

- [x] **Step 3: Run RED selected benchmark fixture**

```bash
python -m qa_z benchmark --fixture executor_bridge_missing_action_context_inputs --json
```

Expected: fail because `executor_bridge.stdout_mentions_action_context` or
`executor_bridge.stdout_mentions_missing_action_context` is missing from actual
results.

### Task 2: Implement Stdout Benchmark Summary

**Files:**
- Modify: `src/qa_z/benchmark.py`

- [x] **Step 1: Import stdout renderer**

Import `render_bridge_stdout` beside `create_executor_bridge`.

- [x] **Step 2: Summarize stdout diagnostics**

Inside `summarize_executor_bridge_actual()`, render stdout from the manifest and
add:

```python
"stdout_mentions_action_context": (
    f"Action context inputs: {len(action_context)}" in stdout
),
"stdout_mentions_missing_action_context": (
    "Missing action context:" in stdout
    and all(missing_path in stdout for missing_path in missing_context)
),
```

- [x] **Step 3: Run GREEN selected benchmark fixture**

```bash
python -m qa_z benchmark --fixture executor_bridge_missing_action_context_inputs --json
```

Expected: pass with `fixtures_passed: 1`, `fixtures_total: 1`, `overall_rate: 1.0`.

### Task 3: Sync Truth Surfaces

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Update user-facing docs**

Document that benchmark executor-bridge fixtures now pin human stdout
diagnostics in addition to manifest and guide diagnostics.

- [x] **Step 2: Update current-truth assertions and gate snapshot if needed**

If the full pytest count changes, update the alpha closure snapshot and matching
truth assertion.

### Task 4: Verify

**Files:**
- Test only

- [x] **Step 1: Run focused checks**

```bash
python -m pytest tests/test_benchmark.py tests/test_current_truth.py -q
python -m qa_z benchmark --fixture executor_bridge_action_context_inputs --json
python -m qa_z benchmark --fixture executor_bridge_missing_action_context_inputs --json
```

Expected: tests pass and both selected fixtures pass.

- [x] **Step 2: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If formatting is needed, format only touched files and rerun affected checks.
