# P5-C Mixed-Language Benchmark Design

## Goal

Add deterministic benchmark coverage for mixed Python and TypeScript post-repair verification outcomes.

## Scope

P5-C is verification-centered. It uses pre-seeded `.qa-z/runs/baseline/fast/summary.json` and `.qa-z/runs/candidate/fast/summary.json` artifacts instead of executing Python or TypeScript tools. This keeps the benchmark focused on verdict logic and avoids coupling it to local `pytest`, `ruff`, `tsc`, `eslint`, or `vitest` installations.

## Fixture Set

The corpus adds four fixtures:

- `mixed_py_resolved_ts_regressed_candidate`: Python blocker resolves and TypeScript typecheck regresses, expecting `mixed`.
- `mixed_ts_resolved_py_regressed_candidate`: TypeScript test blocker resolves and Python lint regresses, expecting `mixed`.
- `mixed_all_resolved_candidate`: Python and TypeScript blockers both resolve, expecting `improved`.
- `mixed_partial_resolved_with_regression_candidate`: one blocker resolves, one remains, and another TypeScript check regresses, expecting `mixed`.

## Contracts

Each fixture declares both `python` and `typescript` in `repo/qa-z.yaml`, keeps `fast.checks` empty because no execution is required, and supplies one `expected.json` with an `expect_verify` contract. The important asserted fields are `verdict`, `blocking_before`, `blocking_after`, `resolved_count`, `new_issue_count`, `regression_count`, and `schema_version`.

## Non-Goals

P5-C does not add live executor behavior, automatic code repair, new deep engines, Semgrep mixed-language findings, or runtime TypeScript/Python tool execution.

## Verification

Use TDD by first adding a corpus-contract test in `tests/test_benchmark.py`, confirming it fails because the fixtures are absent, then adding fixtures until the test passes. Validate the fixture behavior with `python -m qa_z benchmark` for the four P5-C fixtures and finish with `python -m pytest`.
