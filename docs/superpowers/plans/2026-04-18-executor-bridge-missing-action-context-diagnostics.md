# Executor Bridge Missing Action Context Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make missing executor bridge action-context paths visible in guides and pin that diagnostic path in the benchmark corpus.

**Architecture:** Treat missing action context as optional diagnostic residue. The production bridge keeps recording `inputs.action_context_missing`, guide renderers display those missing paths, and the benchmark runner summarizes guide visibility so a committed fixture can catch future drift.

**Tech Stack:** Python standard library, pytest, QA-Z executor bridge, QA-Z benchmark runner, Markdown docs.

---

### Task 1: Pin Missing Context Guide Behavior

**Files:**
- Modify: `tests/test_executor_bridge.py`

- [x] **Step 1: Write the failing unit test**

Add a test after `test_executor_bridge_copies_repair_action_context_inputs` that:

```python
def test_executor_bridge_guides_show_missing_action_context_inputs(
    tmp_path: Path,
) -> None:
    loop_id, _session_id = prepare_autonomy_session(tmp_path)
    outcome_path = tmp_path / ".qa-z" / "loops" / loop_id / "outcome.json"
    outcome = json.loads(outcome_path.read_text(encoding="utf-8"))
    action = outcome["actions_prepared"][0]
    action["context_paths"] = [
        ".qa-z/runs/candidate/verify/summary.json",
        ".qa-z/runs/candidate/verify/missing-context.json",
    ]
    write_json(outcome_path, outcome)

    result = create_executor_bridge(
        root=tmp_path,
        from_loop=loop_id,
        bridge_id="bridge-missing-context",
        now=NOW,
    )

    bridge_dir = tmp_path / ".qa-z" / "executor" / "bridge-missing-context"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    guide = (bridge_dir / "executor_guide.md").read_text(encoding="utf-8")
    codex = (bridge_dir / "codex.md").read_text(encoding="utf-8")
    claude = (bridge_dir / "claude.md").read_text(encoding="utf-8")

    assert manifest["inputs"]["action_context_missing"] == [
        ".qa-z/runs/candidate/verify/missing-context.json"
    ]
    for text in (guide, codex, claude):
        assert "Action context missing" in text
        assert ".qa-z/runs/candidate/verify/missing-context.json" in text
```

- [x] **Step 2: Run RED**

```bash
python -m pytest tests/test_executor_bridge.py::test_executor_bridge_guides_show_missing_action_context_inputs -q
```

Expected: fail because guides do not render missing action context yet.

### Task 2: Implement Guide Rendering

**Files:**
- Modify: `src/qa_z/executor_bridge.py`

- [x] **Step 1: Add missing-context helper**

Add `bridge_missing_action_context_inputs(manifest)` next to
`bridge_action_context_inputs(manifest)`. It should return ordered non-empty
strings from `manifest["inputs"]["action_context_missing"]`.

- [x] **Step 2: Render missing context in human guide**

In `render_executor_bridge_guide`, after copied action context, append:

```python
missing_action_context = bridge_missing_action_context_inputs(manifest)
if missing_action_context:
    lines.append("- Action context missing:")
    lines.extend(f"  - `{path}`" for path in missing_action_context)
```

- [x] **Step 3: Render missing context in executor-specific guides**

In `render_executor_specific_guide`, after copied action context, append:

```python
missing_action_context = bridge_missing_action_context_inputs(manifest)
if missing_action_context:
    lines.extend(["## Action Context Missing", ""])
    lines.extend(f"- `{path}`" for path in missing_action_context)
    lines.append("")
```

- [x] **Step 4: Run GREEN**

```bash
python -m pytest tests/test_executor_bridge.py::test_executor_bridge_guides_show_missing_action_context_inputs -q
```

Expected: pass.

### Task 3: Add Benchmark Expectation And Fixture

**Files:**
- Modify: `tests/test_benchmark.py`
- Modify: `src/qa_z/benchmark.py`
- Add: `benchmarks/fixtures/executor_bridge_missing_action_context_inputs/expected.json`
- Add: `benchmarks/fixtures/executor_bridge_missing_action_context_inputs/repo/qa-z.yaml`
- Add: `benchmarks/fixtures/executor_bridge_missing_action_context_inputs/repo/qa/contracts/contract.md`
- Add: `benchmarks/fixtures/executor_bridge_missing_action_context_inputs/repo/src/app.py`
- Add: `benchmarks/fixtures/executor_bridge_missing_action_context_inputs/repo/.qa-z/runs/baseline/fast/summary.json`
- Add: `benchmarks/fixtures/executor_bridge_missing_action_context_inputs/repo/.qa-z/runs/candidate/fast/summary.json`

- [x] **Step 1: Add compare expectation test**

Extend `test_compare_expected_supports_executor_bridge_expectations` so it
expects a mismatch for `guide_mentions_missing_action_context`.

- [x] **Step 2: Extend benchmark summarizer**

Add `guide_mentions_missing_action_context` to
`summarize_executor_bridge_actual()`. It should be true only when the guide
contains `Action context missing` and every missing context path.

- [x] **Step 3: Add fixture**

Create a fixture that runs `verify` and `executor_bridge` with:

```json
"context_paths": [
  ".qa-z/runs/candidate/verify/summary.json",
  ".qa-z/runs/candidate/verify/missing-context.json"
]
```

Expect one copied context, one missing context, copied file existence, copied
guide visibility, and missing guide visibility.

- [x] **Step 4: Add committed-corpus assertion**

Assert `executor_bridge_missing_action_context_inputs` exists, has
`action_context_missing_count == 1`, and pins
`guide_mentions_missing_action_context == true`.

- [x] **Step 5: Run focused benchmark checks**

```bash
python -m pytest tests/test_benchmark.py::test_compare_expected_supports_executor_bridge_expectations tests/test_benchmark.py::test_committed_benchmark_corpus_has_executor_bridge_action_context_fixture -q
python -m qa_z benchmark --fixture executor_bridge_missing_action_context_inputs --json
```

Expected: pass after implementation.

### Task 4: Sync Truth Surfaces

**Files:**
- Modify: `README.md`
- Modify: `docs/benchmarking.md`
- Modify: `docs/reports/current-state-analysis.md`
- Modify: `docs/reports/next-improvement-roadmap.md`
- Modify: `docs/reports/worktree-commit-plan.md`
- Modify: `tests/test_current_truth.py`

- [x] **Step 1: Document fixture and count**

Mention `executor_bridge_missing_action_context_inputs` alongside
`executor_bridge_action_context_inputs` and update the benchmark count from 48
to 49.

- [x] **Step 2: Pin docs in current-truth tests**

Update current-truth assertions for the new fixture name, missing-context guide
wording, `49/49 fixtures`, and the latest formatter count after final gates.

### Task 5: Verify

**Files:**
- Test only

- [x] **Step 1: Run focused tests**

```bash
python -m pytest tests/test_executor_bridge.py tests/test_benchmark.py tests/test_current_truth.py -q
python -m qa_z benchmark --fixture executor_bridge_missing_action_context_inputs --json
```

Expected: focused tests pass and selected fixture passes.

- [x] **Step 2: Run full gates**

```bash
python -m pytest
python -m qa_z benchmark --json
python -m ruff check .
python -m ruff format --check --no-cache .
python -m mypy src tests
```

Expected: all gates pass. Update the recorded full pytest and benchmark counts
only after this fresh full run.
