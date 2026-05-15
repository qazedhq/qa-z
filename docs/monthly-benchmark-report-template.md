# Monthly Benchmark Report Template

## Month

`YYYY-MM`

## Report Boundary

This report is evidence-backed. Do not claim adoption, user impact,
performance, security impact, customer usage, package publishing, production
deployment, hosted automation, or leaderboard ranking unless the claim is
sourced and approved.

## Summary

- Fixtures selected:
- Fixtures passed:
- Fixtures failed:
- Overall benchmark status:
- New regressions:
- Resolved regressions:
- Not comparable rows:
- Generated results directory:
- Frozen evidence decision:

## Fixture Row Template

Every benchmark row should point to the fixture contract and the QA-Z artifacts
used for the verdict. A row without artifact pointers is not publication-ready.

| Fixture | Lane | Expected contract | Baseline artifact | Candidate artifact | Verify artifact | Verdict | Provenance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `improved_candidate` | verify | `benchmarks/fixtures/improved_candidate/expected.json` | `.qa-z/runs/baseline/fast/summary.json` | `.qa-z/runs/candidate/fast/summary.json` | `.qa-z/runs/candidate/verify/compare.json` | `improved` | committed fixture |

Use the fixture name as the row id. Use the lane to name the measured flow, such
as `fast`, `deep`, `repair`, `verify`, `executor-bridge`, or `executor-result`.

## Artifact Evidence

Each row should link to or name the evidence paths that apply:

- fixture directory;
- `benchmarks/fixtures/<fixture>/expected.json`;
- `benchmarks/fixtures/<fixture>/repo/`;
- `benchmarks/results/work/<fixture>/repo/.qa-z/`;
- generated or seeded baseline run artifacts;
- generated or seeded candidate run artifacts;
- `.qa-z/runs/baseline/fast/summary.json`;
- `.qa-z/runs/baseline/deep/summary.json`;
- `.qa-z/runs/baseline/deep/results.sarif`;
- `.qa-z/runs/baseline/repair/codex.md`;
- `.qa-z/runs/candidate/fast/summary.json`;
- `.qa-z/runs/candidate/deep/summary.json`;
- `.qa-z/runs/candidate/verify/summary.json`;
- `.qa-z/runs/candidate/verify/compare.json`;
- `.qa-z/runs/candidate/verify/report.md`;
- `repair/packet.json`, `repair/handoff.json`, or `repair/codex.md` when
  repair evidence is part of the fixture;
- `deep/results.sarif` when SARIF evidence is part of the fixture.

## Fixture Provenance

Each benchmark row must say whether the evidence is:

- executed during this benchmark run;
- pre-seeded under a fixture repository;
- generated under `benchmarks/results/work/<fixture>/repo/.qa-z/`;
- intentionally frozen with context;
- local-only generated output that must not be committed.

Use fixture paths such as:

```text
benchmarks/fixtures/<fixture>/expected.json
benchmarks/fixtures/<fixture>/repo/
benchmarks/results/work/<fixture>/repo/.qa-z/
```

expected.json is the fixture contract. Benchmark generated output is not the
source of truth unless the report explicitly freezes it with context.

## Validation Commands

Use the narrowest relevant command first:

```bash
python -m qa_z benchmark --fixture <fixture> --json
python -m qa_z benchmark --results-dir benchmarks/results-ci --json
python -m pytest tests/test_launch_growth_package.py -q
python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public
git diff --check
```

When the report references generated `benchmarks/results/**`, record:

- command;
- exit code;
- generated results directory;
- whether `summary.json` and `report.md` were local-only or intentionally frozen;
- reason for freezing, if frozen.

## Claims Boundary

Do not claim:

- adoption numbers;
- active users;
- customer usage;
- production deployment;
- performance improvement;
- security impact;
- leaderboard ranking;
- model quality superiority;
- package publishing;
- hosted automation;

unless the claim is backed by sourced evidence and approved for publication.

Prefer safe wording:

- "The benchmark fixture passed."
- "The verify verdict was `improved`."
- "The fixture row points to QA-Z artifacts."
- "This report does not claim customer adoption or production impact."

## Generated Artifact Policy

Do not commit generated benchmark output by default:

- `benchmarks/results/work/**`;
- `benchmarks/results/summary.json`;
- `benchmarks/results/report.md`;
- root `.qa-z/**`;
- `.pytest_cache/**`;
- `.mypy_cache/**`;
- `.ruff_cache/**`.

Generated benchmark outputs are local by default. Commit them only when
intentionally frozen with surrounding context.

Fixture-local frozen evidence is allowed only under:

```text
benchmarks/fixtures/**/repo/.qa-z/**
```

Use `docs/benchmarking.md` for benchmark fixture layout and
`docs/generated-vs-frozen-evidence-policy.md` for the full generated-artifact
policy.
