# P21 History Residue Fallback Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Synthesize dry-run residue from session-local executor history when the explicit dry-run summary is missing.

**Architecture:** Move pure dry-run verdict logic into a shared helper, then reuse it from `executor-result dry-run`, `repair_session`, and publish summary loaders.

**Tech Stack:** Python, pytest, Markdown docs

---

### Task 1: Add failing fallback tests

- [ ] Add a repair-session verification test that writes history without a dry-run summary and expects synthesized residue
- [ ] Add a publish-summary test that expects the same synthesized residue

### Task 2: Implement the fallback

- [ ] Extract pure dry-run logic into a shared helper module
- [ ] Reuse the helper from `executor_dry_run.py`
- [ ] Synthesize dry-run context from history in `repair_session.py`
- [ ] Reuse that synthesized context in `verification_publish.py`

### Task 3: Update docs and validate

- [ ] Document the history-only fallback in README and artifact schema
- [ ] Record the milestone in `docs/mvp-issues.md`
- [ ] Run focused tests plus full validation
