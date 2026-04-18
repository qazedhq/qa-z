# Mixed Fast Deep Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an executed mixed Python/TypeScript fast-plus-deep repair handoff fixture to the committed benchmark corpus and sync current-truth docs.

**Architecture:** Reuse the existing benchmark runner and expectation sections. Add one fixture with deterministic helper commands and fake Semgrep payloads. Do not modify runner behavior unless the fixture exposes a real contract bug.

**Tech Stack:** Python standard library, pytest, QA-Z benchmark fixture JSON, Markdown docs.

---

### Task 1: Pin The Corpus Gap

**Files:**
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`

- [ ] **Step 1: Add failing corpus assertions**

Require `mixed_fast_deep_handoff_dual_surface` in the mixed-surface realism fixture set. Assert that its expected contract runs fast, deep, and repair handoff, includes both `py_test` and `ts_type`, requires at least two blocking deep findings, and keeps `src/invoice.ts` in handoff affected files.

- [ ] **Step 2: Add failing current-truth assertions**

Require README, benchmarking docs, current-state report, and roadmap to mention the fixture.

- [ ] **Step 3: Run focused tests**

Run:

```bash
python -m pytest tests/test_benchmark.py -k mixed_surface_realism -q
python -m pytest tests/test_current_truth.py -k mixed_fast_deep -q
```

Expected: both fail until fixture and docs are added.

### Task 2: Add The Executed Fixture

**Files:**
- Add: `benchmarks/fixtures/mixed_fast_deep_handoff_dual_surface/expected.json`
- Add: `benchmarks/fixtures/mixed_fast_deep_handoff_dual_surface/repo/qa-z.yaml`
- Add: `benchmarks/fixtures/mixed_fast_deep_handoff_dual_surface/repo/.qa-z-benchmark/semgrep.json`
- Add: `benchmarks/fixtures/mixed_fast_deep_handoff_dual_surface/repo/qa/contracts/contract.md`
- Add: `benchmarks/fixtures/mixed_fast_deep_handoff_dual_surface/repo/src/app.py`
- Add: `benchmarks/fixtures/mixed_fast_deep_handoff_dual_surface/repo/src/invoice.ts`
- Add: `benchmarks/fixtures/mixed_fast_deep_handoff_dual_surface/repo/tests/test_app.py`

- [ ] **Step 1: Configure mixed fast checks**

Declare Python and TypeScript languages. Configure `py_test` and `ts_type` to fail through `benchmarks/support/fast_check.py`.

- [ ] **Step 2: Configure deep check**

Use `benchmarks/support/fake_semgrep.py` and a fixture-local Semgrep JSON payload with one blocking finding in `src/app.py` and one in `src/invoice.ts`.

- [ ] **Step 3: Write expectation contract**

Assert fast, deep, handoff, and artifact outputs with subset matching for lists.

- [ ] **Step 4: Run the fixture**

Run:

```bash
python -m qa_z benchmark --fixture mixed_fast_deep_handoff_dual_surface --json
```

Expected: one fixture passes.

### Task 3: Sync Current-Truth Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [ ] **Step 1: Update benchmark claims**

Describe the fixture as executed mixed fast plus deep handoff coverage, not as a new deep engine or live executor surface.

- [ ] **Step 2: Narrow the roadmap gap**

Record that the first mixed fast plus deep executed fixture has landed. Leave remaining breadth as denser variants, smart-selection combinations, and dry-run history combinations.

- [ ] **Step 3: Run current-truth tests**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

### Task 4: Validate The Baseline

**Files:**
- All touched files

- [ ] **Step 1: Run targeted tests**

Run:

```bash
python -m pytest tests/test_benchmark.py tests/test_current_truth.py -q
```

Expected: pass.

- [ ] **Step 2: Run full tests**

Run:

```bash
python -m pytest
```

Expected: pass.

- [ ] **Step 3: Run full benchmark**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: all committed fixtures pass.
