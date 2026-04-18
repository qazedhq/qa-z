# QA-Z Benchmarking

The QA-Z benchmark corpus is a seeded evaluation set for checking whether the current control plane behaves consistently across fast checks, Semgrep-backed deep findings, repair handoff generation, and post-repair verification.

It is not a live repair loop. It does not call Codex, Claude, remote APIs, queues, or schedulers. Fixtures either run deterministic local QA-Z flows or compare pre-seeded run artifacts.

## Running The Benchmark

Run the committed corpus from the repository root:

```bash
python -m qa_z benchmark
```

The command writes:

```text
benchmarks/results/summary.json
benchmarks/results/report.md
benchmarks/results/work/
```

`summary.json` is the machine-readable source of truth and includes a compact `snapshot` string such as `22/22 fixtures, overall_rate 1.0`. `report.md` is the human-readable companion. `work/` contains isolated copies of fixture repositories and generated QA-Z artifacts; it is disposable scratch output.

Useful variants:

```bash
python -m qa_z benchmark --json
python -m qa_z benchmark --fixture semgrep_eval
python -m qa_z benchmark --fixtures-dir benchmarks/fixtures --results-dir benchmarks/results
```

The exit code is `0` only when every selected fixture passes its expected-result contract.

## Fixture Layout

Each fixture lives under `benchmarks/fixtures/<name>/`:

```text
benchmarks/
  fixtures/
    py_type_error/
      expected.json
      repo/
        qa-z.yaml
        qa/contracts/contract.md
        src/app.py
```

The runner copies `repo/` into `benchmarks/results/work/<name>/repo` before execution, then injects shared helpers from `benchmarks/support/`. Fixtures should stay small and intentional; they are test vectors, not demo applications.

## Expected Contract

`expected.json` declares which QA-Z flows to run and which outcomes must be observed. List expectations use subset matching so fixtures can assert important evidence without becoming brittle.

Supported expectation sections:

- `expect_fast`: fast run status, schema version, failed check ids, blocking failed check ids
- `expect_deep`: deep run status, schema version, finding counts, blocking/filtered/grouped count thresholds, rule ids, filter reasons, policy metadata, and config-error surfacing
- `expect_handoff`: repair-needed flag, target ids, target sources, affected files, validation command ids, schema version
- `expect_verify`: verdict, schema version, blocking before/after, resolved count, remaining issue count, new issue count, regression count
- `expect_artifacts`: generated artifact paths relative to the fixture workspace

Numeric keys ending in `_min` or `_max` are threshold checks. Other scalar keys are exact checks.

For deep policy fixtures, `rule_ids_present` and `rule_ids_absent` compare against the normalized active or grouped findings that remain after ignore-rule and exclude-path policy is applied. Filtered findings are still counted in `findings_count` and `filtered_findings_count`, but their rule ids are not retained in the final active `rule_ids` list. Use `expect_config_error: true` when a fixture must prove an invalid Semgrep configuration surfaces as an execution error instead of looking like a clean no-finding run.

## Initial Corpus

The corpus covers these high-signal cases:

- `py_type_error`
- `py_test_failure`
- `py_lint_failure`
- `ts_lint_failure`
- `ts_type_error`
- `ts_test_failure`
- `ts_multiple_fast_failures`
- `semgrep_eval`
- `semgrep_shell_true`
- `semgrep_hardcoded_secret`
- `deep_severity_threshold_warn_filtered`
- `deep_ignore_rule_suppressed`
- `deep_exclude_paths_skipped`
- `deep_grouped_findings_dedup`
- `deep_filtered_vs_blocking_counts`
- `deep_config_error_surface`
- `fast_and_deep_blocking`
- `unchanged_candidate`
- `improved_candidate`
- `regressed_candidate`
- `ts_unchanged_candidate`
- `ts_regressed_candidate`

The fast fixtures use deterministic helper commands so the benchmark is not coupled to local `ruff`, `mypy`, `pytest`, `eslint`, `tsc`, or `vitest` behavior. The Semgrep fixtures use a deterministic local `semgrep` stand-in that emits normalized Semgrep JSON, which exercises QA-Z deep normalization without requiring Semgrep to be installed.

## Adding A Fixture

1. Create `benchmarks/fixtures/<name>/expected.json`.
2. Add a minimal `repo/qa-z.yaml` with only the checks required for the case.
3. Add a small contract under `repo/qa/contracts/contract.md`.
4. Add only the source, test, seeded `.qa-z/runs`, or `.qa-z-benchmark/semgrep.json` files needed by the expected flows.
5. Run `python -m qa_z benchmark --fixture <name>`.
6. Run `python -m pytest tests/test_benchmark.py`.

Keep expectations explicit enough to catch contract drift, but tolerant enough that unrelated artifact details do not break the benchmark.
