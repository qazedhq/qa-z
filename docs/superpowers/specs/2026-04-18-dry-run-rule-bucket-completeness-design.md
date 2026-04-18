# Dry-Run Rule Bucket Completeness Design

Date: 2026-04-18

## Context

Executor dry-run summaries now expose three deterministic rule id buckets:

- `clear_rule_ids`
- `attention_rule_ids`
- `blocked_rule_ids`

The actual dry-run summarizer already records all three buckets, but many
committed executor dry-run benchmark fixtures only pin counts and selected
attention or blocked ids. That lets a future rule rename, rule movement, or
missing clear rule hide behind unchanged counts.

The gap became more visible after `executor_history_recorded` was added. Empty
history now has a meaningful attention rule, and every non-empty history has one
more clear rule. The benchmark corpus should lock that complete rule partition,
not only partial residue.

## Goal

Require every committed executor dry-run fixture to pin the complete rule id
partition across `clear`, `attention`, and `blocked` buckets.

## Non-Goals

- Do not change dry-run production behavior.
- Do not add new dry-run rules.
- Do not add new benchmark scenarios.
- Do not change verdicts, recommendations, operator summaries, or action ids.
- Do not broaden the live executor surface.

## Design

Add a committed-corpus test in `tests/test_benchmark.py` that checks every
fixture whose name starts with `executor_dry_run_`.

For each fixture, the test requires:

- `clear_rule_ids`, `attention_rule_ids`, and `blocked_rule_ids` are present.
- each bucket has no duplicate rule ids.
- each bucket length matches its matching count field.
- the union of all three buckets equals the known dry-run rule set:
  - `executor_history_recorded`
  - `no_op_requires_explanation`
  - `retry_boundary_is_manual`
  - `mutation_scope_limited`
  - `unrelated_refactors_prohibited`
  - `verification_required_for_completed`
  - `outcome_classification_must_be_honest`

Then update the ten committed executor dry-run fixture expectation files to
include complete buckets. Empty lists are explicit for fixtures with no
attention or blocked rules.

## Documentation

Update current-truth surfaces to say committed dry-run fixtures pin complete
rule buckets as well as operator guidance:

- `README.md`
- `docs/benchmarking.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

Add a current-truth assertion so future docs drift is caught by tests.

## Test Strategy

1. Add the committed-corpus completeness test and run it alone to confirm RED.
2. Add full rule buckets to all executor dry-run `expected.json` files.
3. Run the new benchmark test to confirm GREEN.
4. Add a current-truth assertion and confirm RED.
5. Update docs and confirm GREEN.
6. Run focused tests, full `python -m pytest`, and full
   `python -m qa_z benchmark --json`.
