# Dry-Run Blocked Mixed-History Design

Date: 2026-04-18

## Context

The dry-run safety layer now preserves operator diagnostics for individual
history patterns: clear completion, repeated partial attempts, completed
verification blockers, validation/no-op conflicts, repeated rejected results,
and repeated no-op outcomes.

The remaining benchmark gap is not another command surface. It is mixed-history
coverage: recorded executor history can contain both a top-priority blocked
condition and lower-priority retry or validation signals. The dry-run summary
should keep the blocked verdict and top operator summary, while preserving the
secondary recommended actions that explain what else must be reviewed.

## Goal

Add one deterministic benchmark fixture that proves a completed verification
blocker can coexist with repeated partial attempts and validation conflict
history without dropping any operator action residue.

## Non-Goals

- Do not add live executor orchestration.
- Do not change the dry-run command surface.
- Do not invent a new expectation format.
- Do not broaden into many combinatorial fixtures in this pass.

## Fixture

Add `executor_dry_run_blocked_mixed_history_operator_actions`.

The seeded session history has three attempts:

1. partial accepted attempt
2. second partial accepted attempt
3. completed attempt that remains `verify_blocked` with a validation warning

Expected dry-run signals:

- `repeated_partial_attempts`
- `completed_verify_blocked`
- `validation_conflict`

Expected verdict behavior:

- `verdict`: `blocked`
- `verdict_reason`: `completed_attempt_not_verification_clean`
- `expected_recommendation`: `resolve verification blocking evidence before another completed attempt`
- `operator_summary`: `A completed executor attempt is still blocked by verification evidence.`

Expected action behavior:

- `resolve_verification_blockers`
- `review_validation_conflict`
- `inspect_partial_attempts`

Expected rule counts:

- clear: 3
- attention: 2
- blocked: 1

## Test Strategy

1. Update the committed benchmark corpus test to require the new fixture and its
   action id order.
2. Run the focused test before adding the fixture and confirm it fails because
   the fixture is missing.
3. Add the fixture files and run the fixture benchmark.
4. Update current-truth tests and docs so README, benchmark docs, current-state,
   and roadmap mention the mixed-history fixture.
5. Run focused tests, full pytest, and full benchmark.

## Safety Boundary

The fixture runs only `qa-z executor-result dry-run` against committed local
history artifacts. It does not mutate code, call agents, perform retries, or
contact a network service.
