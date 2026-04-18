# Dry-Run Retry And No-Op Benchmark Density Design

Date: 2026-04-18

## Goal

Close the next dry-run benchmark density gap by adding committed fixtures for
the two remaining retry/no-op operator action mappings:

- repeated rejected executor results
- repeated no-op executor results

This keeps the live-free safety dry-run protected by executable benchmark
evidence without adding live execution, orchestration, or new dry-run logic.

## Current Context

The dry-run logic already emits deterministic signals and actions for:

- `repeated_rejected_attempts` -> `inspect_rejected_results`
- `repeated_no_op_attempts` -> `inspect_no_op_pattern`

The benchmark corpus currently covers clear, repeated partial, completed
verification-blocked, and validation-conflict plus missing no-op histories. It
does not yet pin repeated rejected or repeated no-op histories.

## Scope

Add two fixtures:

1. `executor_dry_run_repeated_rejected_operator_actions`
   - two rejected ingest attempts
   - expected signal: `repeated_rejected_attempts`
   - expected action id: `inspect_rejected_results`

2. `executor_dry_run_repeated_noop_operator_actions`
   - two accepted no-op attempts with no missing-explanation warning
   - expected signal: `repeated_no_op_attempts`
   - expected action id: `inspect_no_op_pattern`

Both fixtures should run through the existing `qa-z executor-result dry-run`
benchmark path.

## Non-Goals

- no production logic changes unless tests expose a real missing summary field
- no live executor calls
- no retry automation
- no new benchmark category
- no generated benchmark result commit

## Acceptance Criteria

- committed corpus tests require both new fixture names
- each fixture pins verdict, reason, history signals, rule counts, operator
  summary, recommended action ids, and recommended action summaries
- docs list the new fixtures and explain the denser operator-action coverage
- `python -m pytest` passes
- `python -m qa_z benchmark --json` passes with the expanded corpus
