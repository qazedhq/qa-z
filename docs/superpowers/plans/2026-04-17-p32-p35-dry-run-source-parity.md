# P32-P35 Dry-Run Source Parity Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make dry-run provenance self-describing in artifacts, visible in human repair-session status output, and covered by benchmark expectations.

**Architecture:** Add one additive field to persisted dry-run summaries, thread it into status rendering, extend benchmark expectation aliasing, and prove the behavior with focused tests plus one corpus fixture update.

**Tech Stack:** Python, pytest, benchmark fixture JSON, Markdown docs

---

### Task 1: Write failing provenance-parity tests

- [ ] Extend repair-session status tests to require a dry-run source line
- [ ] Add benchmark expectation tests for `expected_source`
- [ ] Add direct dry-run command coverage for persisted `summary_source`

### Task 2: Implement the additive artifact and status behavior

- [ ] Persist `summary_source: materialized` in dry-run summaries
- [ ] Render dry-run source in human `repair-session status`
- [ ] Keep JSON/status/session/publish surfaces aligned

### Task 3: Extend benchmark realism coverage

- [ ] Map `expected_source` to `summary_source` in benchmark comparisons
- [ ] Update at least one executor dry-run fixture expected contract to pin provenance

### Task 4: Sync docs and validate

- [ ] Update README, artifact schema, and milestone tracking if wording changes
- [ ] Run focused tests, then full format/lint/typecheck/pytest/benchmark validation
