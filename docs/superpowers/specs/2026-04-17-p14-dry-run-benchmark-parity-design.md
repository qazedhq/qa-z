# P14 Dry-Run Benchmark Parity Design

## Goal

Bring the benchmark dry-run surface up to parity with the richer P13 diagnostics so regressions in `verdict_reason` and rule-status counts are benchmarked instead of only being covered by direct command tests.

## Scope

Included:

- additive benchmark normalization for dry-run `verdict_reason`
- additive benchmark normalization for dry-run rule-status counts
- committed fixture expectations for the three existing dry-run fixtures
- benchmark docs updates for the expanded expectation keys

Excluded:

- new dry-run fixture categories
- benchmark contract redesign
- live executor work
- broader operator policy changes

## Design

### 1. Benchmark Actual Shape

Extend the normalized `executor_dry_run` benchmark actual summary with:

- `verdict_reason`
- `clear_rule_count`
- `attention_rule_count`
- `blocked_rule_count`

These values are already produced by the current dry-run artifact, so the benchmark only needs to expose them.

### 2. Expectation Contract

Keep using `expect_executor_dry_run`.

Additive keys:

- `verdict_reason`
- `clear_rule_count`
- `attention_rule_count`
- `blocked_rule_count`

No alias layer is needed because these are already stable machine fields.

### 3. Committed Fixture Updates

Update the existing dry-run fixtures so they also pin:

- clear fixture: `history_clear` and six clear rules
- repeated partial fixture: `manual_retry_review_required` and one attention rule
- completed verify blocked fixture: `completed_attempt_not_verification_clean` and one blocked rule

### 4. Reporting And Summary

No new top-level benchmark category is needed. These expectations still count under `policy`.

## Validation

- `python -m pytest tests/test_benchmark.py -q`
- `python -m qa_z benchmark --fixture executor_dry_run_clear_verified_completed --json`
- `python -m qa_z benchmark --fixture executor_dry_run_repeated_partial_attention --json`
- `python -m qa_z benchmark --fixture executor_dry_run_completed_verify_blocked --json`
- `python -m qa_z benchmark --json`

## Expected Outcome

After P14, benchmark regressions in dry-run reasoning will surface even if the top-level verdict stays the same.
