# Executor Dry-Run Operator Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the primary dry-run operator action as a stable `operator_decision` id across dry-run, repair-session, publish, and benchmark surfaces.

**Architecture:** Add one pure helper to `executor_dry_run_logic`, then propagate the field through existing additive dry-run residue paths. Keep all existing fields and rule semantics unchanged.

**Tech Stack:** Python, pytest, JSON benchmark fixtures, Markdown docs.

---

### Task 1: Pin The New Contract

**Files:**
- Modify: `tests/test_executor_dry_run_logic.py`
- Modify: `tests/test_executor_result.py`
- Modify: `tests/test_repair_session.py`
- Modify: `tests/test_verification_publish.py`
- Modify: `tests/test_benchmark.py`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Add failing pure-logic assertions**

Assert `operator_decision` for clear, repeated partial, validation conflict, completed verify-blocked, and empty-history summaries.

- [x] **Step 2: Add failing CLI/report assertions**

Assert `qa-z executor-result dry-run --json` includes `operator_decision`, human stdout prints `Decision: <id>`, and `dry_run_report.md` renders `Operator decision`.

- [x] **Step 3: Add failing repair-session and publish assertions**

Assert status JSON, completed session summary, outcome Markdown, and publish Markdown expose `executor_dry_run_operator_decision`.

- [x] **Step 4: Add failing benchmark/current-truth assertions**

Assert committed dry-run fixtures pin `operator_decision`, benchmark actual summaries compare it, and docs mention `operator_decision`.

- [x] **Step 5: Verify RED**

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py tests/test_executor_result.py::test_executor_result_dry_run_reports_clear_for_verified_completed_history tests/test_executor_result.py::test_executor_result_dry_run_reports_attention_for_repeated_partial_history tests/test_repair_session.py::test_repair_session_status_json_includes_synthesized_dry_run tests/test_repair_session.py::test_repair_session_verify_existing_candidate_writes_outcome tests/test_verification_publish.py tests/test_benchmark.py::test_committed_executor_dry_run_fixtures_pin_operator_action_residue tests/test_current_truth.py::test_current_truth_docs_cover_dry_run_publish_and_session_residue -q
```

Expected: fail because the new field is not implemented or documented.

### Task 2: Implement Operator Decision

**Files:**
- Modify: `src/qa_z/executor_dry_run_logic.py`
- Modify: `src/qa_z/executor_dry_run.py`
- Modify: `src/qa_z/cli.py`
- Modify: `src/qa_z/repair_session.py`
- Modify: `src/qa_z/reporters/verification_publish.py`
- Modify: `src/qa_z/benchmark.py`

- [x] **Step 1: Add `operator_decision` helper**

Add a pure helper that returns the primary action id using the same signal priority as `next_recommendation` and `recommended_actions`.

- [x] **Step 2: Add field to dry-run summaries**

Include `"operator_decision": operator_decision(verdict, signals)` in `build_dry_run_summary`.

- [x] **Step 3: Render the field**

Render `Operator decision` in dry-run reports and `Decision` in `executor-result dry-run` human stdout.

- [x] **Step 4: Propagate additive residue**

Backfill missing `operator_decision` in `enrich_dry_run_operator_fields`, copy it into repair-session status/summary/outcome fields as `executor_dry_run_operator_decision`, and carry it into `SessionPublishSummary`.

- [x] **Step 5: Include benchmark actual summaries**

Add `operator_decision` to `summarize_executor_dry_run_actual`.

### Task 3: Update Fixture Expectations And Docs

**Files:**
- Modify: `benchmarks/fixtures/executor_dry_run_*/expected.json`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/repair-sessions.md`
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`

- [x] **Step 1: Add `operator_decision` to committed dry-run fixture expectations**

Use the dominant action id already implied by each fixture's `recommended_action_ids`.

- [x] **Step 2: Document the new field**

Mention `operator_decision` as a compact primary decision id beside operator summary and recommended actions.

- [x] **Step 3: Verify GREEN**

Run the RED command again and confirm it passes.

### Task 4: Full Verification

**Files:**
- Read verification output only.

- [x] **Step 1: Run focused executor dry-run tests**

```bash
python -m pytest tests/test_executor_dry_run_logic.py tests/test_executor_result.py tests/test_repair_session.py tests/test_verification_publish.py tests/test_benchmark.py::test_committed_executor_dry_run_fixtures_pin_operator_action_residue tests/test_current_truth.py::test_current_truth_docs_cover_dry_run_publish_and_session_residue -q
```

Expected: pass.

- [x] **Step 2: Run full tests**

```bash
python -m pytest
```

Expected: all tests pass with the repository's expected skipped test count.

- [x] **Step 3: Run benchmark**

```bash
python -m qa_z benchmark --json
```

Expected: all committed benchmark fixtures pass.
