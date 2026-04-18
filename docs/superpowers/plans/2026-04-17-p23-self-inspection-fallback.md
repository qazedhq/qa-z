# P23 Self-Inspection Fallback Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reuse history-only dry-run synthesis inside self-inspection and backlog generation.

**Architecture:** Call the shared dry-run logic from `discover_executor_history_candidates()`, preserve fallback provenance in evidence, and add a focused regression test.

**Tech Stack:** Python, pytest, Markdown docs

---

### Task 1: Add the failing self-inspection fallback test

- [ ] Seed repeated executor history without `dry_run_summary.json`
- [ ] Assert `self-inspect` promotes `executor_dry_run_attention` and fallback evidence

### Task 2: Implement the synthesis

- [ ] Reuse the shared dry-run helper from `self_improvement.py`
- [ ] Label synthesized evidence distinctly from materialized dry-run summaries

### Task 3: Update docs and validate

- [ ] Update README and milestone status notes
- [ ] Run focused self-inspection tests and full validation
