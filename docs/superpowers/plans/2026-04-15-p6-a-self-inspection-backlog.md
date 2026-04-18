# P6-A Self-Inspection Backlog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an artifact-driven self-inspection and improvement backlog layer for QA-Z.

**Architecture:** Keep the feature additive in `src/qa_z/self_improvement.py`, with dataclasses for reports, backlog items, selections, and artifact paths. The CLI remains a thin adapter that writes `.qa-z/loops/latest/*`, `.qa-z/improvement/backlog.json`, and `.qa-z/loops/history.jsonl`.

**Tech Stack:** Python dataclasses, JSON artifacts, argparse CLI, pytest.

---

### Task 1: Self-Inspection And Backlog Tests

**Files:**
- Create: `tests/test_self_improvement.py`

- [ ] Write tests that seed benchmark, verify, session, and docs artifacts.
- [ ] Assert self-inspection writes `self_inspect.json` and updates `backlog.json`.
- [ ] Assert no-evidence repositories still produce empty deterministic artifacts.
- [ ] Assert scoring uses grounded bonuses and recurrence counts.

### Task 2: Core Self-Improvement Module

**Files:**
- Create: `src/qa_z/self_improvement.py`

- [ ] Define artifact kinds, categories, and dataclasses.
- [ ] Implement JSON loading that skips unreadable optional artifacts without fabricating evidence.
- [ ] Implement candidate discovery from benchmark failures, verification verdicts, incomplete sessions, publish artifact gaps, docs/schema drift indicators, and benchmark fixture coverage gaps.
- [ ] Merge candidates into a stable backlog with timestamps, recurrence counts, status, and priority score.

### Task 3: Selection And History

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [ ] Select the top 1 to 3 open backlog items by priority score and deterministic tie-breakers.
- [ ] Write `selected_tasks.json` and `loop_plan.md`.
- [ ] Append loop memory to `.qa-z/loops/history.jsonl`.

### Task 4: CLI Wiring

**Files:**
- Modify: `src/qa_z/cli.py`
- Modify: `tests/test_cli.py`

- [ ] Add `self-inspect`, `select-next`, and `backlog --json`.
- [ ] Keep human output path-focused and honest about artifact-only planning.

### Task 5: Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`

- [ ] Document evidence sources, scoring, selection, loop memory, and future autonomy work.
- [ ] State that this pass does not call live executors or edit code autonomously.

### Task 6: Validation

**Commands:**
- `python -m pytest tests/test_self_improvement.py`
- `python -m pytest tests/test_cli.py`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy src tests`
- `python -m pytest`
