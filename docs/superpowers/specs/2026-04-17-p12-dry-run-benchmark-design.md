# P12 Dry-Run Benchmark Design

## Goal

Extend the benchmark corpus so the landed `executor-result dry-run` and session-local executor-result history surfaces are protected by deterministic regression tests.

## Scope

Included:

- additive benchmark contract support for executor-result dry-run expectations
- deterministic benchmark execution for dry-run fixtures
- a small committed dry-run fixture set covering `clear`, `attention_required`, and `blocked`
- public docs updates describing the new benchmark surface

Excluded:

- live executor work
- retry scheduling or redispatch policy
- benchmark contract redesign
- richer operator diagnostics beyond the current dry-run summary fields

## Design

### 1. Additive Contract Extension

Add one new optional benchmark section:

- `expect_executor_dry_run`

It follows the existing tolerant comparison style instead of introducing a parallel schema.

Initial supported expectation keys:

- `verdict`
- `evaluated_attempt_count`
- `latest_result_status`
- `latest_ingest_status`
- `history_signals`
- `expected_recommendation`
- `attention_rule_ids`
- `blocked_rule_ids`
- `clear_rule_ids`
- `schema_version`

These map cleanly to the current dry-run summary without needing to compare full report prose.

### 2. Fixture Execution

Add `run.executor_result_dry_run` support to the benchmark runner. The runner should resolve one session reference and call the existing `run_executor_result_dry_run()` implementation.

This path should be independent from `run.executor_result`, but compatible with it. A fixture may use:

- only `executor_result_dry_run` against seeded session history
- only `executor_result`
- both, when a fixture wants to benchmark ingest plus dry-run together later

### 3. Actual Summary Shape

The benchmark actual section should expose a compact normalized summary such as:

- `kind`
- `schema_version`
- `session_id`
- `evaluated_attempt_count`
- `latest_attempt_id`
- `latest_result_status`
- `latest_ingest_status`
- `verdict`
- `history_signals`
- `next_recommendation`
- `attention_rule_ids`
- `blocked_rule_ids`
- `clear_rule_ids`

This keeps list-based comparison stable and machine-checkable.

### 4. Benchmark Category Treatment

Do not add a new benchmark category yet.

Dry-run fixtures should count under the existing `policy` category because they evaluate the frozen executor safety rules. That keeps summary shape stable while still exposing meaningful coverage growth.

### 5. Initial Fixture Set

Add a focused high-signal set:

1. `executor_dry_run_clear_verified_completed`
   - one clean completed attempt
   - verdict `clear`
   - no history signals

2. `executor_dry_run_repeated_partial_attention`
   - repeated partial attempts
   - verdict `attention_required`
   - `retry_boundary_is_manual` in attention rules

3. `executor_dry_run_completed_verify_blocked`
   - completed attempt with verification blocked or mixed
   - verdict `blocked`
   - `verification_required_for_completed` in blocked rules

These fixtures can use seeded repair-session manifests plus `executor_results/history.json` inputs. They should remain fully local and deterministic.

## Validation

- `python -m pytest tests/test_benchmark.py -q`
- `python -m pytest tests/test_executor_result.py -q`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy src tests`
- `python -m pytest`
- `python -m qa_z benchmark --json`

## Expected Outcome

After P12, benchmark coverage will stop treating dry-run/history as an unguarded side surface. Regressions in dry-run verdicts, rule classification, or history interpretation will show up in the same local benchmark loop as the rest of QA-Z.
