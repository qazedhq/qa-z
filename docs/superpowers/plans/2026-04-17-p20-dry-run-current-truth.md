# P20 Dry-Run Current-Truth Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align docs and current-truth tests with landed dry-run publish and residue behavior.

**Architecture:** Update the public README and artifact schema reference first, then pin the new statements with a narrow current-truth regression test.

**Tech Stack:** Markdown docs, pytest

---

### Task 1: Update docs

- [ ] Amend the GitHub summary and dry-run README sections
- [ ] Document the additive repair-session summary fields in `docs/artifact-schema-v1.md`
- [ ] Record P18 through P20 in `docs/mvp-issues.md`

### Task 2: Add current-truth protection

- [ ] Add a regression test that asserts README and artifact-schema mention the landed dry-run residue fields

### Task 3: Validate

- [ ] `python -m pytest tests/test_current_truth.py::test_current_truth_docs_cover_dry_run_publish_and_session_residue -q`
