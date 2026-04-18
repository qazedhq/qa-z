# Executor Bridge Safety Rule Count Design

Date: 2026-04-18

## Context

The executor safety rule catalog is now explicit as `EXECUTOR_SAFETY_RULE_IDS`.
Executor bridge manifests already copy the session-local safety package and
summarize it under `safety_package.rule_ids`.

The bridge summary does not currently include a count. That means an operator or
schema consumer must count the list manually to confirm the copied bridge input
contains the complete six-rule frozen safety set.

## Goal

Add `safety_package.rule_count` to executor bridge manifests, derived from the
same ordered `rule_ids` list already stored in the manifest.

## Non-Goals

- Do not change the executor safety package schema.
- Do not change rule ids, requirements, or bridge package layout.
- Do not change dry-run behavior.
- Do not add live executor behavior.

## Design

Update `bridge_safety_package_summary()` in
`src/qa_z/executor_bridge.py` to return:

```python
"rule_count": len(rule_ids)
```

Strengthen the bridge test to assert:

- `manifest["safety_package"]["rule_ids"] == list(EXECUTOR_SAFETY_RULE_IDS)`
- `manifest["safety_package"]["rule_count"] == len(EXECUTOR_SAFETY_RULE_IDS)`

This keeps the field additive and deterministic.

## Documentation

Update:

- `README.md`
- `docs/artifact-schema-v1.md`

Add current-truth coverage for the phrase `safety rule count` so schema drift is
caught.

## Test Strategy

1. Add the bridge test assertion and run it to confirm RED because `rule_count`
   is missing.
2. Add `rule_count` to `bridge_safety_package_summary()`.
3. Run the bridge test to confirm GREEN.
4. Add current-truth docs guard and confirm RED.
5. Update docs and confirm GREEN.
6. Run focused tests, full `python -m pytest`, and full
   `python -m qa_z benchmark --json`.
