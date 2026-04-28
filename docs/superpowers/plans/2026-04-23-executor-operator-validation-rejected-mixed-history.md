## Goal

Close the next documented Priority 5 gap by pinning a non-blocked mixed-history
executor dry-run contract that combines `validation_conflict` with repeated
rejected-result retry pressure.

## Context / repo evidence

- `docs/reports/current-state-analysis.md` and
  `docs/reports/next-improvement-roadmap.md` both name the next Priority 5
  slice as a non-blocked mixed-history case that combines validation conflict
  with repeated rejected-result retry pressure.
- `src/qa_z/executor_dry_run_logic.py` already produces a deterministic mixed
  attention outcome for that signal combination: `validation_conflict` remains
  the top-level recommendation while `inspect_rejected_results` and
  `inspect_partial_attempts` stay in ordered recommended actions.
- Existing coverage already pins:
  - repeated rejected retry pressure alone via
    `executor_dry_run_repeated_rejected_operator_actions`
  - validation conflict plus missing no-op explanation via
    `executor_dry_run_validation_noop_operator_actions`
  - broader non-blocked mixed attention via
    `executor_dry_run_mixed_attention_operator_actions`
  - blocked mixed-history priority via
    `executor_dry_run_blocked_mixed_history_operator_actions`
- The remaining gap is narrower: no committed fixture or session publish/outcome
  regression specifically locks the combined
  `validation_conflict + repeated_rejected_attempts` attention path.

## Decision

- Treat this as a contract-hardening package, not a new behavior line, unless a
  failing test shows drift in the existing logic.
- Add failing tests first for:
  - pure dry-run logic
  - benchmark fixture/runtime coverage
  - history-fallback session publish or outcome residue
- Materialize a committed benchmark fixture for the new mixed-history slice and
  reuse it as the deterministic source of truth.
- Refresh continuity docs and current-truth tests so the next session can see
  that Priority 5 coverage now includes this exact mixed-history case.

## Scope

- `src/qa_z/executor_dry_run_logic.py` only if tests expose missing behavior
- `tests/test_executor_dry_run_logic.py`
- `tests/test_benchmark_executor_runtime_operator_actions.py`
- `tests/test_verification_publish_session.py`
- `tests/test_repair_session.py` if repair-session outcome coverage is needed
- `benchmarks/fixtures/executor_dry_run_validation_conflict_repeated_rejected_operator_actions/**`
- `tests/test_current_truth.py`
- `README.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

## Verification Plan

- `python -m pytest -q tests/test_executor_dry_run_logic.py tests/test_benchmark_executor_runtime_operator_actions.py tests/test_verification_publish_session.py tests/test_repair_session.py tests/test_current_truth.py`
- `python -m pytest`
- `python -m qa_z benchmark --json --results-dir %TEMP%\qa-z-l29-full-benchmark`
- `python -m mypy src tests`
- `python -m ruff check .`
- `python -m ruff format --check .`

## Blocker

- type: `AMBIGUITY`
- location: mixed-history Priority 5 surfaces
- symptom: docs point to a concrete next mixed-history slice, but the repo only
  partially pins neighboring combinations
- root cause (hypothesis): earlier loops closed repeated-rejected, blocked
  mixed-history, and general mixed-attention coverage separately without adding
  this exact validation-conflict-plus-rejected-retry combination
- unblock condition: one committed fixture plus logic/session/doc regressions
  pin the exact combination and its ordering
- risk: future changes could silently demote validation-conflict priority or
  drop rejected-result inspection from operator-facing surfaces

## Result

- resolved
- the existing logic contract was already correct; this loop closed the missing
  committed-fixture, publish-regression, benchmark-runtime, and continuity-doc
  coverage around that contract
- the new committed fixture is
  `executor_dry_run_validation_conflict_repeated_rejected_operator_actions`

## Outcome

- QA-Z now pins the non-blocked mixed-history slice where
  `validation_conflict` remains the top operator decision while
  `inspect_rejected_results` and `inspect_partial_attempts` remain ordered
  secondary actions
- the same slice is now committed across dry-run logic regression, benchmark
  runtime coverage, session publish fallback coverage, README/current-state/
  roadmap continuity docs, and current-truth tests
- in-loop blockers were:
  - missing fixture/docs during the first RED pass
  - a later architecture-budget overflow in
    `tests/test_benchmark_executor_runtime_operator_actions.py`
  - a mypy optional-iteration regression in
    `tests/test_verification_publish_session_priority5.py`
- both later blockers resolved after splitting the new benchmark regression
  into `tests/test_benchmark_executor_runtime_priority5.py`, making the publish
  helper iterate over `summary.executor_dry_run_recommended_actions or []`, and
  reformatting the touched files

## Verification Results

- `python -m pytest -q tests/test_executor_dry_run_logic.py tests/test_benchmark_executor_runtime_operator_actions.py tests/test_verification_publish_session.py tests/test_verification_publish_session_priority5.py tests/test_current_truth.py` -> `61 passed`
- `python -m qa_z benchmark --fixture executor_dry_run_validation_conflict_repeated_rejected_operator_actions --json --results-dir %TEMP%\\qa-z-l29-validation-rejected` -> `1/1 fixtures, overall_rate 1.0`
- `python -m pytest -q tests/test_benchmark_executor_runtime_architecture.py tests/test_fast_gate_environment.py tests/test_benchmark_executor_runtime_operator_actions.py tests/test_benchmark_executor_runtime_priority5.py tests/test_verification_publish_session_priority5.py` -> `18 passed`
- `python -m pytest` -> `1143 passed`
- `python -m qa_z benchmark --json --results-dir %TEMP%\\qa-z-l29-full-benchmark` -> `54/54 fixtures, overall_rate 1.0`
- `python -m mypy src tests` -> `Success: no issues found in 497 source files`
- `python -m ruff check .` -> passed
- `python -m ruff format --check .` -> `862 files already formatted`

## Next Focus

- `Priority 2: Generated Versus Frozen Evidence Policy Maintenance`
- keep the post-L29 handoff explicit in `docs/reports/current-state-analysis.md`
  and `docs/reports/next-improvement-roadmap.md` so future sessions do not try
  to reopen this mixed-history slice as still pending
