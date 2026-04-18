# Mixed Fast Deep Third Fixture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a third executed mixed Python/TypeScript fast plus deep benchmark fixture that broadens repair handoff aggregation coverage.

**Architecture:** Reuse the existing benchmark fixture pattern: a small fixture repository, deterministic `.qa-z-benchmark/fast_check.py` commands supplied by benchmark support, fake Semgrep JSON, and `expected.json` assertions compared by the existing benchmark runner. No benchmark runner behavior changes are needed.

**Tech Stack:** Python standard library, pytest, existing QA-Z benchmark runner, fake Semgrep support helper.

---

### Task 1: Pin The New Fixture In Corpus Tests

**Files:**
- Modify: `tests/test_benchmark.py`

- [x] **Step 1: Add corpus assertion**

Extend `test_committed_benchmark_corpus_includes_mixed_surface_realism_cases`
to require `mixed_fast_deep_handoff_py_lint_ts_test_dual_deep` and assert its
fast/deep/handoff expectations.

- [x] **Step 2: Run RED corpus assertion**

```bash
python -m pytest tests/test_benchmark.py::test_committed_benchmark_corpus_has_mixed_surface_realism_fixture_set -q
```

Expected: fail with a missing fixture key because the fixture has not been added.

### Task 2: Add The Fixture

**Files:**
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_py_lint_ts_test_dual_deep/expected.json`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_py_lint_ts_test_dual_deep/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_py_lint_ts_test_dual_deep/repo/.qa-z-benchmark/semgrep.json`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_py_lint_ts_test_dual_deep/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_py_lint_ts_test_dual_deep/repo/src/app.py`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_py_lint_ts_test_dual_deep/repo/src/invoice.ts`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_py_lint_ts_test_dual_deep/repo/tests/invoice.test.ts`

- [x] **Step 1: Add expected contract**

Write an `expected.json` that runs fast, deep, and repair handoff and expects
`py_lint`, `ts_test`, Python eval deep finding, TypeScript secret deep finding,
and a single handoff that includes all affected files.

- [x] **Step 2: Add fixture config**

Write `qa-z.yaml` with two deterministic fast checks:

```json
{"id": "py_lint", "run": ["python", ".qa-z-benchmark/fast_check.py", "fail", "src/app.py:2:5 F821 undefined name eval"], "kind": "lint"}
{"id": "ts_test", "run": ["python", ".qa-z-benchmark/fast_check.py", "fail", "tests/invoice.test.ts:5: expected invoice total to be numeric"], "kind": "test"}
```

and one fake Semgrep deep check.

- [x] **Step 3: Add fixture source files**

Add small Python, TypeScript, and test files referenced by the fast/deep evidence.

- [x] **Step 4: Run GREEN selected fixture**

```bash
python -m qa_z benchmark --fixture mixed_fast_deep_handoff_py_lint_ts_test_dual_deep --json
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

Document the third executed mixed fast plus deep fixture and revise language from
"two" to "three" where it describes the committed corpus.

- [x] **Step 2: Update gate snapshot**

After the full benchmark passes, update the alpha closure snapshot from `49/49`
to `50/50` and update the matching current-truth assertion.

### Task 4: Verify

**Files:**
- Test only

- [x] **Step 1: Run focused checks**

```bash
python -m pytest tests/test_benchmark.py tests/test_current_truth.py -q
python -m qa_z benchmark --fixture mixed_fast_deep_handoff_py_lint_ts_test_dual_deep --json
```

Expected: focused tests pass and the selected fixture passes.

- [x] **Step 2: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. If formatting is needed, format only touched files and rerun affected checks.
