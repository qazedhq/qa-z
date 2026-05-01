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
