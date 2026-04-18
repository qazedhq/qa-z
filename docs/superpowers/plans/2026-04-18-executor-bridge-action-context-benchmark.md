# Executor Bridge Action Context Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add benchmark corpus coverage proving loop-sourced executor bridges copy repair-session action context files into bridge-local inputs.

**Architecture:** Extend benchmark expectations with `expect_executor_bridge`, add a small `run.executor_bridge` execution path, and add one committed fixture that uses seeded baseline/candidate summaries plus generated verification evidence as the copied action context. The existing executor bridge implementation remains the production source of truth.

**Tech Stack:** Python standard library, pytest, QA-Z benchmark runner, existing repair-session and executor-bridge helpers.

---

### Task 1: Pin Executor-Bridge Benchmark Expectations

**Files:**
- Modify: `tests/test_benchmark.py`

- [x] **Step 1: Add compare test for `expect_executor_bridge`**

Add a test that builds a `BenchmarkExpectation` with `expect_executor_bridge` and asserts `compare_expected()` reports a mismatch when `actual["executor_bridge"]` does not match.

- [x] **Step 2: Run RED test**

```bash
python -m pytest tests/test_benchmark.py::test_compare_expected_supports_executor_bridge_expectations -q
```

Expected: fail because the benchmark expectation model currently ignores `expect_executor_bridge`.

### Task 2: Add Committed Fixture Contract

**Files:**
- Add: `benchmarks/fixtures/executor_bridge_action_context_inputs/expected.json`
- Add: `benchmarks/fixtures/executor_bridge_action_context_inputs/repo/qa-z.yaml`
- Add: `benchmarks/fixtures/executor_bridge_action_context_inputs/repo/qa/contracts/contract.md`
- Add: `benchmarks/fixtures/executor_bridge_action_context_inputs/repo/src/app.py`
- Add: `benchmarks/fixtures/executor_bridge_action_context_inputs/repo/.qa-z/runs/baseline/fast/summary.json`
- Add: `benchmarks/fixtures/executor_bridge_action_context_inputs/repo/.qa-z/runs/candidate/fast/summary.json`
- Modify: `tests/test_benchmark.py`

- [x] **Step 1: Add fixture files**

Seed a baseline failed fast summary and a candidate passed fast summary. The fixture should run `verify` first, then run `executor_bridge` with `.qa-z/runs/candidate/verify/summary.json` as action context.

- [x] **Step 2: Add committed-corpus assertion**

Assert the fixture exists and expects `action_context_count == 1`.

- [x] **Step 3: Run selected benchmark RED**

```bash
python -m qa_z benchmark --fixture executor_bridge_action_context_inputs --json
```

Expected: fail because `run.executor_bridge` is not implemented yet.

### Task 3: Implement Benchmark Runner Support

**Files:**
- Modify: `src/qa_z/benchmark.py`

- [x] **Step 1: Extend `BenchmarkExpectation`**

Add `expect_executor_bridge` and an `executor_bridge_config()` helper that reads `baseline_run`, `session_id`, `bridge_id`, `loop_id`, and ordered `context_paths`.

- [x] **Step 2: Add executor bridge execution**

Create a repair session, write a minimal `qa_z.autonomy_outcome` loop artifact with one `repair_session` action, call `create_executor_bridge(... from_loop=loop_id ...)`, and read the resulting manifest and guide.

- [x] **Step 3: Add summarizer and comparison hook**

Summarize bridge kind, schema version, bridge/session/loop ids, prepared action type, action-context source paths, copied paths, missing count, copied-file existence, and guide mention status. Compare that section through `compare_expected()`.

- [x] **Step 4: Run GREEN checks**

```bash
python -m pytest tests/test_benchmark.py::test_compare_expected_supports_executor_bridge_expectations tests/test_benchmark.py::test_committed_benchmark_corpus_has_executor_bridge_action_context_fixture -q
python -m qa_z benchmark --fixture executor_bridge_action_context_inputs --json
```

Expected: tests pass and selected benchmark reports `1/1` fixture passed.

### Task 4: Sync Truth Surfaces

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Document fixture and count**

Mention `executor_bridge_action_context_inputs` as a committed local benchmark fixture and update the full benchmark count from 47 to 48.

- [x] **Step 2: Update current-truth assertions**

Assert README, benchmarking docs, current-state analysis, roadmap, and the alpha closure snapshot mention the new fixture/count.

### Task 5: Verify

**Files:**
- Test only

- [x] **Step 1: Run focused tests**

```bash
python -m pytest tests/test_benchmark.py tests/test_current_truth.py -q
python -m qa_z benchmark --fixture executor_bridge_action_context_inputs --json
```

Expected: focused tests pass and selected benchmark passes.

- [x] **Step 2: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. Update the recorded full pytest and benchmark counts only after this fresh full run.
