# P22 CLI Fallback Parity Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that history-only dry-run fallback reaches the actual CLI surfaces users read.

**Architecture:** Reuse the landed fallback logic without adding new behavior, then add focused CLI regression tests and status docs.

**Tech Stack:** Python, pytest, Markdown docs

---

### Task 1: Add failing CLI parity tests

- [ ] Add a `repair-session status` test for history-only fallback
- [ ] Add a `github-summary` CLI test for history-only fallback

### Task 2: Keep status docs honest

- [ ] Record the new CLI parity coverage in `docs/mvp-issues.md`
- [ ] Write the spec and plan artifacts for the milestone

### Task 3: Validate

- [ ] Run the focused CLI tests
- [ ] Re-run full validation once the parity tests are green
