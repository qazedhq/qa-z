# Dry-Run Operator Benchmark Density Design

Date: 2026-04-18

## Goal

Broaden the benchmark proof surface for executor dry-run operator diagnostics.
The previous pass added `operator_summary` and `recommended_actions` to dry-run,
repair-session, and publish surfaces. This pass makes those diagnostics part of
the benchmark contract so regressions are caught by the seeded corpus.

## Scope

- Expose dry-run operator diagnostic fields in benchmark actual summaries.
- Add one committed dry-run fixture for a mixed attention history:
  validation conflict plus missing no-op explanation.
- Pin both action ids and action summaries in fixture expectations.
- Keep the benchmark live-free: no external executor, no retry loop, no code
  mutation beyond normal fixture copying and artifact writing.

## Fixture Shape

The new fixture is:

`executor_dry_run_validation_noop_operator_actions`

It seeds one repair session with one no-op style executor-result history attempt
that carries both:

- `validation_summary_conflicts_with_results`
- `no_op_without_explanation`

Expected dry-run behavior:

- verdict: `attention_required`
- reason: `classification_conflict_requires_review`
- history signals:
  - `validation_conflict`
  - `missing_no_op_explanation`
- operator summary:
  `Executor history has validation conflicts that need manual review.`
- recommended actions:
  - `review_validation_conflict`
  - `require_no_op_explanation`

## Benchmark Contract Additions

`summarize_executor_dry_run_actual()` should add:

- `operator_summary`
- `recommended_action_ids`
- `recommended_action_summaries`

These are additive benchmark fields. Existing expectations continue to work.

## Docs

README and benchmarking docs should mention the new operator-diagnostics fixture
and explain that dry-run fixtures now pin recommended action residue, not only
verdicts and rule buckets.

## Acceptance Criteria

- A failing test proves benchmark summaries do not yet expose action fields.
- A failing test proves the committed corpus lacks the new fixture.
- The benchmark fixture passes once implementation and fixture data are added.
- `python -m pytest` passes.
- `python -m qa_z benchmark --json` passes with the new fixture count.
