# Mixed Fast Deep Third Fixture Design

## Purpose

The benchmark corpus already has two executed mixed fast plus deep handoff
fixtures:

- `mixed_fast_deep_handoff_dual_surface` covers Python test failure,
  TypeScript type failure, and Python/TypeScript deep findings.
- `mixed_fast_deep_handoff_ts_lint_python_deep` covers TypeScript lint failure
  plus a Python deep finding.

The roadmap still calls out mixed-surface breadth as finite. This pass adds a
third executed fixture that uses a different fast-check mix while preserving the
same deterministic local boundary.

## Scope

- Add `mixed_fast_deep_handoff_py_lint_ts_test_dual_deep`.
- Run deterministic Python lint and TypeScript test failures through the fast
  runner.
- Run fake Semgrep with one Python finding and one TypeScript finding.
- Require one repair handoff to aggregate both fast checks and both deep
  findings.
- Keep fixture count and docs in sync after validation.

## Behavior

The new fixture should produce:

```json
{
  "expect_fast": {
    "status": "failed",
    "blocking_failed_checks": ["py_lint", "ts_test"]
  },
  "expect_deep": {
    "status": "failed",
    "blocking_findings_min": 2
  },
  "expect_handoff": {
    "target_sources": ["fast_check", "deep_finding"],
    "affected_files": ["src/app.py", "tests/invoice.test.ts", "src/invoice.ts"]
  }
}
```

The fixture should stay small and deterministic. The failing checks use
`.qa-z-benchmark/fast_check.py`, and the deep findings use
`.qa-z-benchmark/fake_semgrep.py` with fixture-local `semgrep.json`.

## Non-Goals

- Do not add TypeScript deep automation or a real TypeScript toolchain.
- Do not add live Codex or Claude execution.
- Do not alter repair handoff schema or benchmark comparison semantics.
- Do not add network dependencies.

## Test Strategy

- Add a corpus assertion for the new fixture name and expected fields first.
- Run the assertion to confirm RED because the fixture does not exist yet.
- Add the fixture directory, expected contract, config, contract, and source
  files.
- Run the selected benchmark fixture until it passes.
- Run focused benchmark/current-truth tests and the full alpha gate suite.

## Documentation

Update README, `docs/benchmarking.md`, current-state analysis, roadmap, commit
plan, and current-truth assertions so they say the corpus has three executed
mixed fast plus deep fixtures and the full benchmark count is 50/50.
