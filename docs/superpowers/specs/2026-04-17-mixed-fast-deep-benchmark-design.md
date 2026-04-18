# Mixed Fast Deep Benchmark Design

## Goal

Broaden the benchmark corpus with one executed mixed-surface fixture that proves QA-Z can aggregate Python fast failures, TypeScript fast failures, Semgrep-backed deep findings, and repair handoff targets in the same deterministic run.

## Problem

The corpus already protects Python fast, TypeScript fast, mixed-language verification, Semgrep deep policy, executor-result realism, and a Python-only fast-plus-deep handoff case. The remaining benchmark breadth gap is narrower: there is not yet a committed fixture that executes mixed Python/TypeScript fast failures and deep findings together, then proves the repair handoff keeps all targets visible.

Without that fixture, a regression could still pass the corpus while dropping one surface from the combined handoff.

## Chosen Approach

Add `mixed_fast_deep_handoff_dual_surface` under `benchmarks/fixtures/`.

The fixture repository declares both Python and TypeScript languages and runs:

- `py_test`: deterministic failing Python test check
- `ts_type`: deterministic failing TypeScript type check
- `sg_scan`: deterministic fake Semgrep run with blocking findings in `src/app.py` and `src/invoice.ts`

The expectation contract asserts:

- fast status is failed
- both `py_test` and `ts_type` are blocking failed checks
- deep status is failed with at least two blocking findings
- both Semgrep rule ids are present
- repair handoff has both `fast_check` and `deep_finding` sources
- affected files include both Python and TypeScript source files
- validation command ids include both failed checks plus `qa-z-fast` and `qa-z-deep`

## Why A Fixture Instead Of Runner Changes

The benchmark runner already supports executing fast, deep, and repair handoff flows together. The gap is proof breadth, not missing infrastructure. A fixture gives executable evidence without changing the core engine or widening the alpha surface.

## Non-Goals

- no new benchmark expectation schema
- no TypeScript-specific deep engine
- no live executor, queue, scheduler, or remote orchestration
- no LLM-based judgment
- no generated benchmark result committed as frozen evidence

## Tests

Pin the corpus with:

- a committed-fixture test that requires `mixed_fast_deep_handoff_dual_surface`
- current-truth tests that require README, benchmarking docs, current-state report, and roadmap to mention the fixture
- targeted benchmark execution for the new fixture
- full benchmark execution after implementation
