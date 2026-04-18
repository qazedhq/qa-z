# Mixed Fast Deep Second Fixture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a second executed mixed fast plus deep benchmark fixture that proves TypeScript fast lint evidence and Python deep evidence aggregate into one repair handoff.

**Architecture:** Reuse the existing benchmark fixture contract. The change is data and documentation only: tests pin the expected fixture contract, the fixture supplies deterministic helper inputs, and docs record the expanded current truth.

**Tech Stack:** Python pytest, QA-Z benchmark fixture JSON/YAML, deterministic benchmark support helpers, Markdown docs.

---

### Task 1: Pin Corpus And Docs Expectations

**Files:**
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Add the failing benchmark corpus assertion**

Add `mixed_fast_deep_handoff_ts_lint_python_deep` to the required mixed-surface fixture set. Assert:

```python
mixed_fast_deep_ts_lint = by_name[
    "mixed_fast_deep_handoff_ts_lint_python_deep"
].expectation
assert mixed_fast_deep_ts_lint.run == {
    "fast": True,
    "deep": True,
    "repair_handoff": True,
}
assert mixed_fast_deep_ts_lint.expect_fast["blocking_failed_checks"] == ["ts_lint"]
assert mixed_fast_deep_ts_lint.expect_deep["rule_ids_present"] == [
    "python.lang.security.audit.eval"
]
assert mixed_fast_deep_ts_lint.expect_handoff["target_sources"] == [
    "fast_check",
    "deep_finding",
]
assert "src/app.py" in mixed_fast_deep_ts_lint.expect_handoff["affected_files"]
assert "src/invoice.ts" in mixed_fast_deep_ts_lint.expect_handoff["affected_files"]
```

- [ ] **Step 2: Add the failing current-truth doc assertion**

In `test_mixed_fast_deep_benchmark_breadth_is_documented`, require the new fixture name in README, benchmarking docs, current-state report, and roadmap. Also require the phrase `second mixed fast plus deep executed fixture` in the roadmap.

- [ ] **Step 3: Verify RED**

Run:

```bash
python -m pytest tests/test_benchmark.py::test_committed_benchmark_corpus_has_mixed_surface_realism_fixture_set tests/test_current_truth.py::test_mixed_fast_deep_benchmark_breadth_is_documented -q
```

Expected: fail because the new fixture and docs do not exist yet.

### Task 2: Add The Fixture

**Files:**
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_ts_lint_python_deep/expected.json`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_ts_lint_python_deep/repo/qa-z.yaml`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_ts_lint_python_deep/repo/.qa-z-benchmark/semgrep.json`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_ts_lint_python_deep/repo/qa/contracts/contract.md`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_ts_lint_python_deep/repo/src/app.py`
- Create: `benchmarks/fixtures/mixed_fast_deep_handoff_ts_lint_python_deep/repo/src/invoice.ts`

- [ ] **Step 1: Write deterministic fixture input files**

Use `fast_check.py` to emit a `ts_lint` failure mentioning `src/invoice.ts`. Use `fake_semgrep.py` plus `semgrep.json` to emit one `python.lang.security.audit.eval` finding for `src/app.py`.

- [ ] **Step 2: Write `expected.json`**

Require:

```json
{
  "run": {"fast": true, "deep": true, "repair_handoff": true},
  "expect_fast": {"blocking_failed_checks": ["ts_lint"]},
  "expect_deep": {
    "blocking_findings_min": 1,
    "rule_ids_present": ["python.lang.security.audit.eval"]
  },
  "expect_handoff": {
    "target_sources": ["fast_check", "deep_finding"],
    "affected_files": ["src/app.py", "src/invoice.ts"]
  }
}
```

- [ ] **Step 3: Verify fixture GREEN**

Run:

```bash
python -m pytest tests/test_benchmark.py::test_committed_benchmark_corpus_has_mixed_surface_realism_fixture_set -q
python -m qa_z benchmark --fixture mixed_fast_deep_handoff_ts_lint_python_deep --json
```

Expected: benchmark corpus test passes and the single fixture passes.

### Task 3: Update Current Truth Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Document the second fixture**

Mention `mixed_fast_deep_handoff_ts_lint_python_deep` wherever the first mixed fast plus deep fixture is named.

- [ ] **Step 2: Reframe the roadmap**

Update Priority 3 so it says the second mixed fast plus deep executed fixture is now landed, while further mixed handoff breadth remains possible.

- [ ] **Step 3: Verify docs GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py::test_mixed_fast_deep_benchmark_breadth_is_documented -q
```

Expected: pass.

### Task 4: Full Verification

**Files:**
- Read verification output only.

- [ ] **Step 1: Run focused tests**

```bash
python -m pytest tests/test_benchmark.py::test_committed_benchmark_corpus_has_mixed_surface_realism_fixture_set tests/test_current_truth.py::test_mixed_fast_deep_benchmark_breadth_is_documented -q
```

Expected: pass.

- [ ] **Step 2: Run full tests**

```bash
python -m pytest
```

Expected: all tests pass with the repository's expected skipped test count.

- [ ] **Step 3: Run benchmark**

```bash
python -m qa_z benchmark --json
```

Expected: every committed fixture passes, now including the new second mixed fast plus deep fixture.
