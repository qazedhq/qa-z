# P19 Dry-Run History Residue Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve dry-run attempt residue in completed session summaries, session outcome Markdown, and publish surfaces.

**Architecture:** Reuse the existing session-local dry-run summary as the single source of truth, then copy additive fields into session summary and publish models.

**Tech Stack:** Python, pytest, Markdown docs

---

### Task 1: Add failing repair-session and publish tests

- [ ] Extend repair-session expectations to require dry-run attempt counts and history signals
- [ ] Extend GitHub summary expectations to require the same residue fields

### Task 2: Thread dry-run residue through completed session surfaces

- [ ] Copy attempt count and history signals into `session_summary_dict()`
- [ ] Render the residue fields in `render_outcome_markdown()`
- [ ] Preserve the residue fields in `SessionPublishSummary`
- [ ] Render the residue fields in `render_publish_summary_markdown()`

### Task 3: Validate

- [ ] `python -m pytest tests/test_repair_session.py::test_repair_session_verify_existing_candidate_writes_outcome tests/test_github_summary.py::test_github_summary_includes_repair_session_outcome_when_present -q`
