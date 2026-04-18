# Dry-Run Mixed-Attention Diagnostics Design

## Purpose

Executor dry-run diagnostics already preserve primary actions and secondary recommended actions, including blocked mixed-history cases. The next improvement is to make non-blocked mixed-attention histories easier for operators to read without adding live execution, retry scheduling, or LLM judgment.

## Selected Approach

Use a narrow deterministic diagnostic enhancement:

- keep existing verdict, verdict reason, next recommendation, and action ordering unchanged
- improve `operator_summary` only when multiple non-blocking attention signals are present
- add a benchmark fixture that proves repeated no-op pressure, missing no-op explanation, and validation conflict are all preserved together
- keep benchmark evidence fixture-local under `benchmarks/fixtures/**/repo/.qa-z/**`

This is better than broad rule redesign because the current action ordering is already useful and covered. The missing part is operator explanation, not new safety policy.

## Behavior

Blocked histories keep the existing blocked summaries because scope drift and blocked verification should stay dominant.

For non-blocked attention histories:

- `validation_conflict` plus `missing_no_op_explanation` reports both validation conflict and no-op explanation gaps
- either of those plus repeated retry pressure reports the retry pressure too
- `recommended_actions` remains the detailed action list in priority order
- `next_recommendation` remains the highest-priority next action

The first new pinned case is:

```text
history_signals:
- repeated_no_op_attempts
- validation_conflict
- missing_no_op_explanation

operator_summary:
Executor history has validation conflicts, no-op explanation gaps, and retry pressure; review all recommended actions before another retry.

recommended_action_ids:
- review_validation_conflict
- require_no_op_explanation
- inspect_no_op_pattern
```

## Files

- `src/qa_z/executor_dry_run_logic.py`: add deterministic mixed-attention summary wording
- `tests/test_executor_dry_run_logic.py`: add a RED unit test for mixed attention
- `tests/test_benchmark.py`: require the new fixture in the committed corpus
- `benchmarks/fixtures/executor_dry_run_mixed_attention_operator_actions/**`: add the seeded fixture
- `docs/benchmarking.md`: list the new fixture
- `docs/reports/next-improvement-roadmap.md`: mark the diagnostic depth pass as landed

## Non-Goals

- no live executor invocation
- no automatic retry scheduling
- no changes to ingest acceptance rules
- no changes to verdict priority
- no hidden network dependency

## Verification

Run:

```bash
python -m pytest tests/test_executor_dry_run_logic.py tests/test_benchmark.py -q
python -m qa_z benchmark --fixture executor_dry_run_mixed_attention_operator_actions --json
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```
