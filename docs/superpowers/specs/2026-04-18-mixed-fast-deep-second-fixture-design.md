# Mixed Fast Deep Second Fixture Design

## Goal

Broaden the committed benchmark corpus with a second executed mixed fast plus deep fixture without changing the benchmark runner contract.

## Current Evidence

The corpus already includes `mixed_fast_deep_handoff_dual_surface`, which proves that Python and TypeScript fast failures can be aggregated with Semgrep-backed deep findings in a single repair handoff. The current roadmap still calls out denser mixed fast plus deep interactions beyond that first fixture, so the next hardening step should add breadth rather than a new engine.

## Design

Add `mixed_fast_deep_handoff_ts_lint_python_deep` under `benchmarks/fixtures/`.

The fixture will:

- run the existing deterministic fast helper with a failing `ts_lint` check
- run the existing deterministic fake Semgrep helper with one Python `eval` finding
- request repair handoff generation
- expect fast evidence from `src/invoice.ts`
- expect deep evidence from `src/app.py`
- expect handoff `target_sources` to include both `fast_check` and `deep_finding`
- expect validation commands for `check:ts_lint`, `qa-z-fast`, and `qa-z-deep`

No production benchmark code changes are required. The existing fixture discovery, isolated workspace copy, support-file installation, fast runner, deep runner, and handoff comparison paths already support this shape.

## Documentation Surface

Update README, benchmarking docs, current-state analysis, and next-improvement roadmap so the public current truth says there are now two committed executed mixed fast plus deep fixtures, not only the first dual-surface fixture.

## Tests

Add test coverage before adding the fixture:

- extend the committed benchmark corpus test so it requires `mixed_fast_deep_handoff_ts_lint_python_deep`
- assert the new fixture contract pins `ts_lint`, Python `eval`, dual-source handoff aggregation, and both affected files
- extend current-truth documentation tests so all public docs mention the new fixture

## Non-Goals

- Do not add live Codex or Claude execution.
- Do not add network-dependent benchmark behavior.
- Do not change the benchmark schema or runner behavior.
- Do not broaden this into a new dry-run history fixture in the same pass.

## Acceptance

The work is accepted when the focused benchmark/current-truth tests fail before the fixture and docs exist, then pass after implementation, and `python -m pytest` plus `python -m qa_z benchmark --json` both pass.
