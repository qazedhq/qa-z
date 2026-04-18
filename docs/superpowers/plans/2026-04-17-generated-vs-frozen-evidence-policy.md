# Generated Versus Frozen Evidence Policy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make generated-versus-frozen evidence policy explicit in docs and deterministic self-inspection.

**Architecture:** Keep the policy as a small contract in `qa_z.self_improvement`: `.gitignore` proves local-output enforcement, `docs/generated-vs-frozen-evidence-policy.md` proves the human policy exists, and self-inspection uses both signals before closing stale artifact-policy backlog items. Documentation surfaces point to the same policy file.

**Tech Stack:** Python standard library, pytest, Markdown docs.

---

### Task 1: Pin Policy Snapshot Behavior

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [ ] **Step 1: Write failing tests**

Add tests that create `.gitignore` with generated artifact rules but omit `docs/generated-vs-frozen-evidence-policy.md`; assert `collect_live_repository_signals()` returns `generated_artifact_policy_explicit == False` and `generated_artifact_ignore_policy_explicit == True`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_self_improvement.py -k "generated_artifact_policy" -q`

Expected: failure because the current snapshot treats ignore coverage alone as explicit policy.

- [ ] **Step 3: Implement minimal snapshot fields**

Update `generated_artifact_policy_snapshot()` to return ignore coverage, documented coverage, missing ignore rules, missing document terms, policy doc path, and combined explicit status.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_self_improvement.py -k "generated_artifact_policy" -q`

Expected: tests pass.

### Task 2: Ground Self-Inspection Policy Gaps

**Files:**
- Modify: `tests/test_self_improvement.py`
- Modify: `src/qa_z/self_improvement.py`

- [ ] **Step 1: Write failing tests**

Add one test where `.gitignore` is explicit but the policy doc is missing and report evidence mentions generated versus frozen ambiguity; assert an `evidence_freshness_gap` candidate is emitted with `source == "generated_artifact_policy"`.

Add one test where both `.gitignore` and the policy doc are explicit; assert artifact-policy categories are suppressed when no runtime artifact paths are dirty.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_self_improvement.py -k "policy_gap or stale_artifact_policy" -q`

Expected: failure because missing policy-document evidence is not yet represented.

- [ ] **Step 3: Implement minimal candidate evidence helper**

Add a helper that converts missing ignore rules or missing policy document terms into concise evidence entries. Include that evidence in `discover_evidence_freshness_candidates()`.

- [ ] **Step 4: Run focused tests**

Run: `python -m pytest tests/test_self_improvement.py -k "policy_gap or stale_artifact_policy" -q`

Expected: tests pass.

### Task 3: Document The Policy

**Files:**
- Create: `docs/generated-vs-frozen-evidence-policy.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/benchmarking.md`
- Modify: `README.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `tests/test_current_truth.py`
- Modify: `src/qa_z/autonomy.py`

- [ ] **Step 1: Write failing current-truth tests**

Add assertions that README, schema docs, and benchmarking docs reference `docs/generated-vs-frozen-evidence-policy.md` and the local-default/frozen-only benchmark result rule.

- [ ] **Step 2: Run current-truth test**

Run: `python -m pytest tests/test_current_truth.py -q`

Expected: failure because the new policy file and doc references do not exist yet.

- [ ] **Step 3: Add and sync docs**

Create the policy document and update the docs listed above. Add the policy file to autonomy context paths for `clarify_generated_vs_frozen_evidence_policy`.

- [ ] **Step 4: Run current-truth test**

Run: `python -m pytest tests/test_current_truth.py -q`

Expected: tests pass.

### Task 4: Validate The Slice

**Files:**
- No additional source files.

- [ ] **Step 1: Run targeted tests**

Run: `python -m pytest tests/test_self_improvement.py tests/test_current_truth.py -q`

Expected: all selected tests pass.

- [ ] **Step 2: Run full Python suite**

Run: `python -m pytest`

Expected: all Python tests pass, with the existing skipped count unchanged unless repository state says otherwise.

- [ ] **Step 3: Review changed files**

Run: `git diff -- src/qa_z/self_improvement.py src/qa_z/autonomy.py tests/test_self_improvement.py tests/test_current_truth.py README.md docs/artifact-schema-v1.md docs/benchmarking.md docs/reports/current-state-analysis.md docs/reports/next-improvement-roadmap.md docs/generated-vs-frozen-evidence-policy.md docs/superpowers/specs/2026-04-17-generated-vs-frozen-evidence-policy-design.md docs/superpowers/plans/2026-04-17-generated-vs-frozen-evidence-policy.md`

Expected: only the policy slice is changed by this work.
