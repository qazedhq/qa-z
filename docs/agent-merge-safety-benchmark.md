# Agent Merge Safety Benchmark

The public benchmark story should measure whether agent-written code becomes safe to merge after QA-Z evidence and repair prompts.

## Name

```text
Agent Merge Safety Benchmark
```

## Measurement Loop

```text
agent writes code -> QA-Z detects issue -> repair prompt -> agent fixes -> verify improved
```

## Metrics

- baseline blocking count;
- candidate blocking count;
- `qa-z verify` verdict;
- resolved fast checks;
- resolved deep findings;
- new regressions;
- repair prompt target count;
- time to green.

## Public Leaderboard Scope

The leaderboard should compare workflows, not shame individual contributors. Candidate lanes:

- Codex;
- Claude Code;
- Cursor;
- aider;
- OpenHands;
- Goose;
- human repair baseline.

## Local Evidence

Use QA-Z artifacts as benchmark inputs:

```bash
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

## Monthly Report Provenance

Monthly benchmark reports should connect each published row to both its fixture
and its QA-Z run artifacts. At minimum, include:

- the tracked fixture path, for example
  `benchmarks/fixtures/improved_candidate/expected.json`;
- baseline and candidate run directories under `.qa-z/runs/<run-id>/`;
- the `qa-z verify` summary or report path that supplied the verdict;
- the validation command and captured output used before publishing the report.

Avoid unsourced adoption, performance, or user-impact claims. If a result is a
sample row, label it as a sample and do not present it as monthly production
evidence.
