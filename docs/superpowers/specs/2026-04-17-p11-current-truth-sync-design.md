# P11 Current-Truth Sync Design

## Goal

Tighten QA-Z's current-truth surface so public docs, shipped examples/templates, and local guidance stop diverging on already-landed alpha behavior.

## Scope

This pass stays narrow and additive. It does not add new QA flows or live execution.

Included:

- sync `src/qa_z/config.py` command guidance with the actual `review` and `repair-prompt` implementations
- sync generated benchmark artifact policy by ignoring `benchmarks/results/summary.json` and `benchmarks/results/report.md`
- add regression tests that lock these current-truth expectations in place

Excluded:

- new benchmark fixtures
- workflow behavior redesign
- config-schema expansion
- any live executor, retry, or orchestration work

## Why This Scope

The current repository already documents `qa-z review` and `qa-z repair-prompt` as working surfaces, but the in-repo guidance strings still describe them as scaffolded. That is a quiet source of truth drift.

The worktree-triage docs also explicitly call out generated benchmark summary and report files as local or deferred evidence, while `.gitignore` currently ignores only `benchmarks/results/work/`. That gap makes the repository policy easy to violate accidentally.

These are small issues individually, but they undercut the larger alpha claim that QA-Z prefers explicit contracts and deterministic evidence over implied behavior.

## Design

### 1. Command Guidance Sync

Update `COMMAND_GUIDANCE["review"]` and `COMMAND_GUIDANCE["repair-prompt"]` to describe their actual shipped responsibilities:

- `review`: render run-aware review packets from local artifacts, including sibling deep context when present
- `repair-prompt`: build repair packets and prompt artifacts from failed fast checks and blocking deep findings

The wording should remain honest about being local and deterministic. It should not imply live model execution, code edits, or remote orchestration.

### 2. Benchmark Generated-Artifact Policy Sync

Update `.gitignore` so the repository-level ignore rules match the documented policy:

- keep ignoring `benchmarks/results/work/`
- also ignore `benchmarks/results/summary.json`
- also ignore `benchmarks/results/report.md`
- continue re-allowing fixture-local `.qa-z` inputs under `benchmarks/fixtures/**/repo/.qa-z/**`

This keeps generated benchmark evidence local by default unless a future commit intentionally freezes it.

### 3. Regression Tests

Add a focused current-truth test module that asserts:

- `COMMAND_GUIDANCE["review"]` and `COMMAND_GUIDANCE["repair-prompt"]` no longer contain stale scaffolded wording and do contain current deterministic guidance
- `.gitignore` includes the documented benchmark generated-artifact ignores
- `benchmark/README.md` continues to point users at `benchmarks/` so the singular legacy directory does not drift back into the active surface

These tests keep the sync effort from turning back into silent drift later.

## Risks

- Over-testing prose too literally can become brittle. The tests should lock only the high-signal truth, not every sentence.
- `.gitignore` changes must preserve fixture-local benchmark inputs.

## Validation

- `python -m pytest tests/test_current_truth.py -q`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy src tests`
- `python -m pytest`
- `python -m qa_z benchmark --json`

## Expected Outcome

After P11, QA-Z's docs and shipped guidance will be more internally consistent, and the repository will have explicit tests guarding two high-signal current-truth surfaces that were previously easy to drift.
