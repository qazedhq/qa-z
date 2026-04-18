# Benchmark Report Generated-Policy Sync Design

## Purpose

The benchmark command already writes `benchmarks/results/summary.json`, `benchmarks/results/report.md`, and `benchmarks/results/work/` as local generated artifacts. The next improvement is to make the human-readable `report.md` carry that same policy context so copied or frozen reports remain honest about their evidence status.

## Selected Approach

Use a narrow renderer and documentation sync:

- keep the benchmark summary JSON schema unchanged
- add a generated-output policy section to the Markdown report
- keep the existing category-rate numbers, but label each category as `covered` or `not covered`
- update docs to explain that selected-fixture runs can have uncovered categories

This is better than adding a new summary schema field because the policy is presentation guidance, not a new benchmark result contract.

## Behavior

`render_benchmark_report()` should include a `Generated Output Policy` section before category rates:

```text
## Generated Output Policy

- `benchmarks/results/summary.json` and `benchmarks/results/report.md` are generated benchmark outputs.
- They are local by default; commit them only as intentional frozen evidence with surrounding context.
- `benchmarks/results/work/` is disposable scratch output.
```

Category lines should preserve the existing pass-rate values and append coverage:

```text
- handoff: 0/1 (0.0, covered)
- detection: 0/0 (0.0, not covered)
```

The coverage label means:

- `covered`: at least one selected fixture had an expectation for that category
- `not covered`: no selected fixture exercised that category in the current run

## Files

- `src/qa_z/benchmark.py`: render generated-output policy and category coverage labels
- `tests/test_benchmark.py`: pin report policy text and coverage labels
- `docs/benchmarking.md`: describe report policy text and selected-run coverage labels
- `docs/reports/next-improvement-roadmap.md`: mark the report generated-policy sync pass as landed

## Non-Goals

- no benchmark schema version change
- no changes to fixture execution
- no live executor, remote API, scheduler, or agent invocation
- no changes to pass/fail calculations
- no generated artifact committed as frozen evidence

## Verification

Run:

```bash
python -m pytest tests/test_benchmark.py::test_render_benchmark_report_includes_generated_policy_and_category_coverage -q
python -m pytest tests/test_current_truth.py tests/test_benchmark.py -q
python -m qa_z benchmark --json
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
```
