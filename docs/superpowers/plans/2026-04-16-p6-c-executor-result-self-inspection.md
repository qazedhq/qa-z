# P6-C Executor Result Self-Inspection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach QA-Z self-inspection to read executor-result artifacts and turn partial, failed, or no-op external execution outcomes into backlog candidates for the next loop.

**Architecture:** Keep the change additive inside `src/qa_z/self_improvement.py`. Reuse session manifests and stored `executor_result.json` artifacts as evidence, create explicit executor-result backlog categories, and document the new evidence source without changing the public command names.

**Tech Stack:** Python dataclasses, JSON artifacts, argparse CLI, pytest.

---

### Task 1: Red Tests

**Files:**
- Modify: `tests/test_self_improvement.py`

- [ ] Add a fixture helper that writes a repair session with stored executor-result metadata.
- [ ] Add a failing self-inspection test that expects executor-result backlog categories for `partial`, `failed`, and `no_op` outcomes.
- [ ] Add a scoring test that proves executor-result evidence gets grounded priority boosts for validation failure or no-op safety concerns.
- [ ] Run the targeted self-improvement tests and confirm they fail for the missing feature.

### Task 2: Executor-Result Candidate Discovery

**Files:**
- Modify: `src/qa_z/self_improvement.py`

- [ ] Discover stored `executor_result.json` artifacts from sessions and classify them into explicit executor-result backlog categories.
- [ ] Attach evidence summaries that include executor status, validation status, and verification hint.
- [ ] Add deterministic recommendations for partial reruns, failed execution triage, and no-op safety review.
- [ ] Extend scoring bonuses only where grounded by the recorded signals.

### Task 3: Documentation Sync

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`

- [ ] Update the self-inspection description so executor-result artifacts are part of the evidence set.
- [ ] Document the new backlog/history categories or signals introduced by executor-result evidence.

### Task 4: Validation

**Commands:**
- `python -m pytest tests/test_self_improvement.py`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy src tests`
- `python -m pytest`
- `python -m qa_z benchmark --json`
