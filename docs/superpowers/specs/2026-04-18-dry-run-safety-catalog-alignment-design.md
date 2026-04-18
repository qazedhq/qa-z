# Dry-Run Safety Catalog Alignment Design

Date: 2026-04-18

## Context

The dry-run rule catalog is now exported as `DRY_RUN_RULE_IDS`. That catalog is
the seven-rule runtime audit set used by `executor-result dry-run`.

Its relationship to the frozen pre-live executor safety package is currently
documented but not directly tested:

- the safety package has six frozen rules
- dry-run adds one runtime audit rule, `executor_history_recorded`
- therefore the dry-run catalog should equal one dry-run-only rule plus the
  ordered safety package rule ids

If the safety package changes later, the dry-run catalog should drift loudly
instead of silently falling out of sync.

## Goal

Make the relationship between the dry-run catalog and the executor safety
package executable:

```text
DRY_RUN_RULE_IDS == DRY_RUN_ONLY_RULE_IDS + executor_safety_package().rules[*].id
```

## Non-Goals

- Do not change safety package contents.
- Do not change dry-run rule behavior, statuses, verdicts, summaries, or
  recommendations.
- Do not add new dry-run fixtures.
- Do not import the safety package into runtime dry-run evaluation.

## Design

Add a small exported tuple in `src/qa_z/executor_dry_run_logic.py`:

```python
DRY_RUN_ONLY_RULE_IDS = ("executor_history_recorded",)
```

Keep `DRY_RUN_RULE_IDS` as the explicit ordered catalog. Add a unit test that:

1. reads ordered rule ids from `executor_safety_package()["rules"]`
2. asserts `DRY_RUN_ONLY_RULE_IDS == ("executor_history_recorded",)`
3. asserts `DRY_RUN_RULE_IDS == DRY_RUN_ONLY_RULE_IDS + safety_rule_ids`

This keeps runtime logic simple while making catalog drift visible in tests.

## Documentation

Update docs to say the dry-run rule catalog extends the frozen safety package
with exactly one dry-run-only audit rule:

- `README.md`
- `docs/benchmarking.md`
- `docs/artifact-schema-v1.md`

Add a current-truth assertion for `extends the frozen safety package`.

## Test Strategy

1. Add the new import and alignment test, then run it to confirm RED because
   `DRY_RUN_ONLY_RULE_IDS` is not exported yet.
2. Add `DRY_RUN_ONLY_RULE_IDS`.
3. Run the focused logic test to confirm GREEN.
4. Add current-truth docs guard and confirm RED.
5. Update docs and confirm GREEN.
6. Run focused tests, full `python -m pytest`, and full
   `python -m qa_z benchmark --json`.
