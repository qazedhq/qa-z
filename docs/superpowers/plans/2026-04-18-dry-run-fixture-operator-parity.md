# Dry-Run Fixture Operator Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every committed executor dry-run benchmark fixture pin deterministic operator summary and recommended action residue.

**Architecture:** This is a benchmark-contract hardening pass. It adds a corpus-level invariant test, backfills missing `expected.json` fields, and updates current-truth docs without changing dry-run production behavior.

**Tech Stack:** Python, pytest, QA-Z benchmark fixtures, Markdown docs.

---

## Files

- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`
- Modify: `benchmarks/fixtures/executor_dry_run_clear_verified_completed/expected.json`
- Modify: `benchmarks/fixtures/executor_dry_run_repeated_partial_attention/expected.json`
- Modify: `benchmarks/fixtures/executor_dry_run_completed_verify_blocked/expected.json`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

## Task 1: Add The Failing Corpus Invariant

- [ ] **Step 1: Add the invariant test**

Add this test after `test_committed_benchmark_corpus_has_executor_dry_run_fixture_set` in `tests/test_benchmark.py`:

```python
def test_committed_executor_dry_run_fixtures_pin_operator_action_residue() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    dry_run_fixtures = [
        fixture for fixture in fixtures if fixture.name.startswith("executor_dry_run_")
    ]

    assert dry_run_fixtures

    missing: list[str] = []
    for fixture in dry_run_fixtures:
        expected = fixture.expectation.expect_executor_dry_run
        for key in (
            "operator_summary",
            "recommended_action_ids",
            "recommended_action_summaries",
        ):
            if not expected.get(key):
                missing.append(f"{fixture.name}:{key}")

    assert missing == []
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_executor_dry_run_fixtures_pin_operator_action_residue" -q
```

Expected: failure listing missing operator residue keys for the original dry-run fixtures.

## Task 2: Backfill Fixture Expectations

- [ ] **Step 1: Update clear completed fixture**

Add these fields to `benchmarks/fixtures/executor_dry_run_clear_verified_completed/expected.json` inside `expect_executor_dry_run`:

```json
"operator_summary": "Executor history is clear under the pre-live safety rules.",
"recommended_action_ids": [
  "continue_standard_verification"
],
"recommended_action_summaries": [
  "Continue normal verification and review; no immediate dry-run safety concern is recorded."
]
```

- [ ] **Step 2: Update repeated partial fixture**

Add these fields to `benchmarks/fixtures/executor_dry_run_repeated_partial_attention/expected.json` inside `expect_executor_dry_run`:

```json
"operator_summary": "Repeated partial executor attempts need manual review before another retry.",
"recommended_action_ids": [
  "inspect_partial_attempts"
],
"recommended_action_summaries": [
  "Review unresolved repair targets across repeated partial attempts before retrying."
]
```

- [ ] **Step 3: Update completed verify blocked fixture**

Add these fields to `benchmarks/fixtures/executor_dry_run_completed_verify_blocked/expected.json` inside `expect_executor_dry_run`:

```json
"operator_summary": "A completed executor attempt is still blocked by verification evidence.",
"recommended_action_ids": [
  "resolve_verification_blockers",
  "review_validation_conflict"
],
"recommended_action_summaries": [
  "Review verify/summary.json and repair remaining or regressed blockers before accepting completion.",
  "Compare executor validation claims with deterministic verification artifacts before retrying."
]
```

- [ ] **Step 4: Run the focused test and confirm GREEN**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "committed_executor_dry_run_fixtures_pin_operator_action_residue" -q
```

Expected: pass.

## Task 3: Update Current-Truth Documentation Tests And Docs

- [ ] **Step 1: Add current-truth assertions**

Extend `test_executor_dry_run_retry_noop_benchmark_density_is_documented` in
`tests/test_current_truth.py`:

```python
    assert "all committed executor dry-run fixtures" in benchmarking
    assert "operator summary and recommended action residue" in readme
    assert "all committed dry-run fixtures" in current_state
    assert "all committed dry-run fixtures" in roadmap
```

- [ ] **Step 2: Run current-truth tests and confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: failure until the docs are updated.

- [ ] **Step 3: Update docs**

Update README, benchmark docs, current-state report, and roadmap so they clearly
say the dry-run corpus now pins operator summary and recommended action residue
across all committed dry-run fixtures.

- [ ] **Step 4: Run current-truth tests and confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 4: Verify The Hardened Contract

- [ ] **Step 1: Run focused benchmark tests**

Run:

```bash
python -m pytest tests/test_benchmark.py -k "executor_dry_run or compare_expected_supports_executor_dry_run_expectations" -q
```

Expected: pass.

- [ ] **Step 2: Run affected fixtures sequentially**

Run these one at a time:

```bash
python -m qa_z benchmark --fixture executor_dry_run_clear_verified_completed --json
python -m qa_z benchmark --fixture executor_dry_run_repeated_partial_attention --json
python -m qa_z benchmark --fixture executor_dry_run_completed_verify_blocked --json
```

Expected: each selected fixture passes.

- [ ] **Step 3: Run full tests**

Run:

```bash
python -m pytest
```

Expected: all tests pass except the existing skipped test.

- [ ] **Step 4: Run full benchmark**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: every committed fixture passes.

## VCS Note

This plan intentionally does not include staging or committing. The active
workspace already contains many unrelated local changes, and this pass should
leave integration control to the operator.
