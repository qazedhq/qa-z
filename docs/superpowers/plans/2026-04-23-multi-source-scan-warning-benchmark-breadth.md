# Multi-Source Scan Warning Benchmark Breadth Plan

**Goal:** Close the proof gap between README's claimed benchmark breadth and the
current benchmark/report/current-truth surfaces by landing explicit multi-source
Semgrep scan-warning coverage across corpus tests, report rendering, and
continuity docs.

**Context / repo evidence:**

- `README.md` already says the benchmark corpus includes both
  `deep_scan_warning_diagnostics` and
  `deep_scan_warning_multi_source_diagnostics`.
- The fixture itself is already committed:
  `benchmarks/fixtures/deep_scan_warning_multi_source_diagnostics/expected.json`
  expects two warning sources, two paths, and two types.
- `src/qa_z/runners/semgrep.py` plus `src/qa_z/benchmark_run_summaries.py`
  already preserve those warning signals as `scan_warning_*` and
  `scan_quality_*`.
- The remaining gap is higher up the stack: `tests/test_benchmark_corpus.py`,
  `tests/test_benchmark_reporting.py`, `docs/benchmarking.md`,
  `docs/reports/current-state-analysis.md`, and
  `docs/reports/next-improvement-roadmap.md` still underspecify that
  multi-source warning breadth even though README claims it.
- `src/qa_z/benchmark_report_details.py` currently renders only
  `scan_quality_*` fields, so the human report path is less robust than the
  broader deep-warning contract that already talks about both raw
  `scan_warning_*` and summary-level `scan_quality`.

**Decision:**

- Keep the current Semgrep normalization and benchmark summary flow; no runner
  redesign is needed.
- Add a new executed mixed-surface benchmark fixture that combines a fast
  failure with non-blocking multi-source deep scan warnings, proving that deep
  warning provenance survives an attached fast+deep+handoff path without
  inventing a deep repair target.
- Harden benchmark report rendering so warning provenance falls back to raw
  `scan_warning_*` fields when `scan_quality_*` is absent, keeping the human
  report aligned with the broader benchmark contract.
- Sync benchmark corpus tests and continuity docs so README no longer overstates
  a breadth slice that narrower surfaces fail to pin.

**Scope:**

- Add or extend benchmark fixture/test coverage for multi-source scan warnings.
- Update benchmark report rendering/tests for raw warning fallback and
  multi-source human output.
- Sync README-adjacent benchmark docs and continuity docs to the new breadth
  slice.

## Verification Plan

- `python -m pytest -q tests/test_benchmark_report_details.py tests/test_benchmark_reporting.py tests/test_benchmark_corpus.py`
- `python -m qa_z benchmark --fixture deep_scan_warning_multi_source_diagnostics --json --results-dir <temp-dir>`
- `python -m qa_z benchmark --fixture mixed_fast_deep_scan_warning_fast_only --json --results-dir <temp-dir>`
- `python -m pytest -q tests/test_current_truth.py`
- `python -m ruff check src/qa_z/benchmark_report_details.py tests/test_benchmark_report_details.py tests/test_benchmark_reporting.py tests/test_benchmark_corpus.py tests/test_current_truth.py`

## Follow-up

- After the package closes, refresh `docs/reports/current-state-analysis.md` and
  `docs/reports/next-improvement-roadmap.md` with the landed fourth executed
  mixed fast+deep breadth slice.

## Blocker

- type: `TEST`
- location: `tests/test_current_truth.py`
- symptom: the current-truth breadth assertion still pinned README wording to
  "three executed mixed fast plus deep handoff fixtures" after the fourth mixed
  fixture landed
- root cause (hypothesis): continuity coverage had not been refreshed to the
  new mixed-surface breadth wording even though README/docs moved forward
- unblock condition: sync current-truth wording plus benchmark/docs references
  to the four-fixture corpus
- risk: stale continuity coverage could report the broadened benchmark slice as
  undocumented even when the implementation and public docs were aligned
- follow-up blocker: `python -m ruff format --check .` reported formatting drift
  in `tests/test_benchmark_corpus.py` and `tests/test_current_truth.py` after
  the doc/current-truth sync
- follow-up unblock condition: format the touched tests and rerun the format
  gate so the package does not close with an avoidable style blocker

## Outcome

- `render_deep_warning_lines()` now falls back to raw `scan_warning_*` fields
  when `scan_quality_*` summary fields are absent, so benchmark reports stay
  aligned with the broader deep-warning contract.
- `mixed_fast_deep_scan_warning_fast_only` is now committed and executed,
  proving an attached fast+deep+handoff run can keep non-blocking multi-source
  scan warnings visible while repair handoff remains fast-only.
- README, benchmarking docs, current-state, roadmap, and current-truth coverage
  now all name the fourth mixed fast+deep fixture and the multi-source warning
  benchmark slice explicitly.

## Verification Results

- `python -m pytest -q tests/test_benchmark_report_details.py tests/test_benchmark_reporting.py tests/test_benchmark_corpus.py` -> `23 passed`
- `python -m pytest -q tests/test_current_truth.py -k "semgrep_scan_warning_diagnostics_are_documented or mixed_fast_deep_benchmark_breadth_is_documented"` -> `2 passed`
- `python -m qa_z benchmark --fixture deep_scan_warning_multi_source_diagnostics --json --results-dir %TEMP%\qa-z-l26-multi-source-warning` -> `1/1 fixtures, overall_rate 1.0`
- `python -m qa_z benchmark --fixture mixed_fast_deep_scan_warning_fast_only --json --results-dir %TEMP%\qa-z-l26-mixed-warning-fast-only` -> `1/1 fixtures, overall_rate 1.0`
- `python -m qa_z benchmark --json --results-dir %TEMP%\qa-z-l26-full-benchmark` -> `53/53 fixtures, overall_rate 1.0`
- `python -m pytest -q` -> `1133 passed`
- `python -m mypy src tests` -> success
- `python -m ruff check src/qa_z/benchmark_report_details.py tests/test_benchmark_report_details.py tests/test_benchmark_reporting.py tests/test_benchmark_corpus.py tests/test_current_truth.py` -> passed
- `python -m ruff format --check .` -> `556 files already formatted`

## Next Focus

- Shift the immediate roadmap focus to Priority 4 report/template/example sync;
  the mixed-surface benchmark breadth package is now closed unless a new
  deterministic slice adds unique evidence.
