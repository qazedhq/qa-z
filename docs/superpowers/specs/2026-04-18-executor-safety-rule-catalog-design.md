# Executor Safety Rule Catalog Design

Date: 2026-04-18

## Context

The dry-run rule catalog now has an exported `DRY_RUN_RULE_IDS` tuple and a
test-proven relationship to the executor safety package. The executor safety
package itself still has no exported rule id catalog; callers must inspect
`executor_safety_package()["rules"]` to recover the ordered six-rule safety set.

That leaves one remaining catalog drift point:

- `executor_safety_package()` emits six rule objects.
- `DRY_RUN_RULE_IDS` should extend those six ids with one dry-run-only rule.
- The six safety ids are not yet available as a small explicit contract.

## Goal

Export the frozen pre-live safety rule id catalog as
`EXECUTOR_SAFETY_RULE_IDS` and use it when composing `DRY_RUN_RULE_IDS`.

## Non-Goals

- Do not change the executor safety package schema.
- Do not change any safety rule id, category, requirement, or enforcement point.
- Do not change dry-run rule behavior.
- Do not add new benchmark fixtures.

## Design

Add a module-level tuple in `src/qa_z/executor_safety.py`:

```python
EXECUTOR_SAFETY_RULE_IDS = (
    "no_op_requires_explanation",
    "retry_boundary_is_manual",
    "mutation_scope_limited",
    "unrelated_refactors_prohibited",
    "verification_required_for_completed",
    "outcome_classification_must_be_honest",
)
```

Update `src/qa_z/executor_dry_run_logic.py` to import that tuple and define:

```python
DRY_RUN_RULE_IDS = DRY_RUN_ONLY_RULE_IDS + EXECUTOR_SAFETY_RULE_IDS
```

Add tests that prove:

- the safety package emits rule ids in exactly `EXECUTOR_SAFETY_RULE_IDS` order
- the dry-run catalog uses `DRY_RUN_ONLY_RULE_IDS + EXECUTOR_SAFETY_RULE_IDS`

## Documentation

Update docs to distinguish the exported six-rule executor safety rule catalog
from the seven-rule dry-run rule catalog:

- `README.md`
- `docs/benchmarking.md`
- `docs/artifact-schema-v1.md`

Add a current-truth assertion for `executor safety rule catalog`.

## Test Strategy

1. Add failing imports/assertions for `EXECUTOR_SAFETY_RULE_IDS`.
2. Run focused tests to confirm RED.
3. Add the constant and wire dry-run catalog to it.
4. Run focused tests to confirm GREEN.
5. Add docs guard, update docs, and rerun current-truth tests.
6. Run focused tests, full `python -m pytest`, and full
   `python -m qa_z benchmark --json`.
