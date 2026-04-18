# P18 Dry-Run Publish Parity Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make GitHub summary output include session dry-run verdict context when it exists.

**Architecture:** Thread dry-run fields from session summary JSON into `SessionPublishSummary`, then render them in `render_publish_summary_markdown()`.

**Tech Stack:** Python, pytest, Markdown docs

---

### Task 1: Add failing GitHub summary tests

- [ ] Extend the session summary fixture helper with dry-run fields
- [ ] Assert the GitHub summary includes dry-run verdict and reason

### Task 2: Implement publish-thread parity

- [ ] Extend `SessionPublishSummary`
- [ ] Load dry-run fields from session summary JSON
- [ ] Render the extra lines for session publish summaries

### Task 3: Validate

- [ ] `python -m pytest tests/test_github_summary.py -q`
