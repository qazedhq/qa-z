# Dry-Run Rule Catalog Design

Date: 2026-04-18

## Context

Executor dry-run fixture expectations now pin complete `clear`, `attention`,
and `blocked` rule id buckets. That closes count-only drift, but the benchmark
contract test still carries its own hard-coded copy of the dry-run rule ids.

The production safety package intentionally has six frozen pre-live executor
rules. Dry-run summaries evaluate those safety rules plus one runtime audit
rule, `executor_history_recorded`, so the dry-run rule set is a distinct
seven-rule catalog.

## Goal

Expose the dry-run rule catalog from `src/qa_z/executor_dry_run_logic.py` and
make tests use that catalog instead of duplicating the same string list.

## Non-Goals

- Do not change dry-run verdicts, rule statuses, summaries, or recommendations.
- Do not change the pre-live executor safety package rule list.
- Do not add new dry-run rules.
- Do not alter benchmark fixture expectations beyond the tests that validate
  them.

## Design

Add a module-level tuple:

```python
DRY_RUN_RULE_IDS = (
    "executor_history_recorded",
    "no_op_requires_explanation",
    "retry_boundary_is_manual",
    "mutation_scope_limited",
    "unrelated_refactors_prohibited",
    "verification_required_for_completed",
    "outcome_classification_must_be_honest",
)
```

Add a logic test that asserts `evaluate_rules([], {})` emits rule ids in exactly
that order. This makes the catalog executable rather than a stale comment.

Update the committed benchmark completeness test to compare fixture bucket
unions against `set(DRY_RUN_RULE_IDS)`.

## Documentation

Update current-truth docs to distinguish:

- the six-rule frozen executor safety package
- the seven-rule dry-run catalog that adds `executor_history_recorded`

Add a current-truth assertion for `dry-run rule catalog` so the distinction does
not drift out of docs.

## Test Strategy

1. Add imports and tests that reference `DRY_RUN_RULE_IDS`, then run focused
   tests to confirm RED because the constant does not exist.
2. Add the constant and update the benchmark test to use it.
3. Run focused tests to confirm GREEN.
4. Add a current-truth assertion and update docs.
5. Run focused tests, full `python -m pytest`, and full
   `python -m qa_z benchmark --json`.
