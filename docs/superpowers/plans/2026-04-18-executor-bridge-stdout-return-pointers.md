# Executor Bridge Stdout Return Pointers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make non-JSON `qa-z executor-bridge` stdout show the result, safety, and verification entrypoints an external operator needs immediately after bridge creation.

**Architecture:** Reuse fields already stored in the bridge manifest. Keep `--json` unchanged, and extend only `render_bridge_stdout()` plus tests and docs.

**Tech Stack:** Python, pytest, QA-Z CLI, executor bridge manifests, Markdown docs.

---

## Files

- Modify: `src/qa_z/executor_bridge.py`
- Modify: `tests/test_executor_bridge.py`
- Modify: `tests/test_current_truth.py`
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`

## Task 1: Add RED CLI Stdout Test

- [ ] **Step 1: Add a non-JSON stdout test**

In `tests/test_executor_bridge.py`, add:

```python
def test_executor_bridge_cli_stdout_points_to_return_and_safety_entrypoints(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loop_id, session_id = prepare_autonomy_session(tmp_path)

    exit_code = main(
        [
            "executor-bridge",
            "--path",
            str(tmp_path),
            "--from-loop",
            loop_id,
            "--bridge-id",
            "bridge-stdout",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "qa-z executor-bridge: ready_for_external_executor" in output
    assert "Executor guide: .qa-z/executor/bridge-stdout/executor_guide.md" in output
    assert "Result template: .qa-z/executor/bridge-stdout/result_template.json" in output
    assert "Expected result: .qa-z/executor/bridge-stdout/result.json" in output
    assert "Safety package: .qa-z/executor/bridge-stdout/inputs/executor_safety.md" in output
    assert f"Safety rule count: {len(EXECUTOR_SAFETY_RULE_IDS)}" in output
    assert (
        "Verify command: python -m qa_z repair-session verify --session "
        f".qa-z/sessions/{session_id} --rerun"
    ) in output
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_executor_bridge.py -k "stdout_points_to_return_and_safety_entrypoints" -q
```

Expected: fail because the current stdout lacks result, safety, and verify
pointers.

## Task 2: Extend Stdout Renderer

- [ ] **Step 1: Update `render_bridge_stdout()`**

In `src/qa_z/executor_bridge.py`, replace `render_bridge_stdout()` with:

```python
def render_bridge_stdout(manifest: dict[str, Any]) -> str:
    """Render human CLI output for bridge creation."""
    return_contract = manifest.get("return_contract")
    if not isinstance(return_contract, dict):
        return_contract = {}
    verify_command = return_contract.get("verify_command")
    lines = [
        "qa-z executor-bridge: ready_for_external_executor",
        f"Bridge: {manifest['bridge_dir']}",
        f"Source session: {manifest['source_session_id']}",
        f"Handoff: {manifest['handoff_path']}",
        f"Executor guide: {manifest['bridge_dir']}/executor_guide.md",
        f"Result template: {return_contract.get('result_template_path')}",
        f"Expected result: {return_contract.get('expected_result_artifact')}",
        f"Safety package: {manifest['safety_package']['policy_markdown']}",
        f"Safety rule count: {bridge_safety_rule_count(manifest)}",
    ]
    if isinstance(verify_command, list):
        lines.append(f"Verify command: {format_command([str(item) for item in verify_command])}")
    return "\n".join(lines)
```

- [ ] **Step 2: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_executor_bridge.py -k "stdout_points_to_return_and_safety_entrypoints" -q
```

Expected: pass.

## Task 3: Current-Truth Documentation

- [ ] **Step 1: Add docs guard**

In `tests/test_current_truth.py`, add:

```python
    assert "bridge stdout return pointers" in readme
    assert "bridge stdout return pointers" in schema
```

- [ ] **Step 2: Confirm RED**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: fail until README and schema mention the new stdout contract.

- [ ] **Step 3: Update docs**

Update:

- `README.md`
- `docs/artifact-schema-v1.md`

Required phrase:

```text
bridge stdout return pointers
```

- [ ] **Step 4: Confirm GREEN**

Run:

```bash
python -m pytest tests/test_current_truth.py -q
```

Expected: pass.

## Task 4: Verification

- [ ] **Step 1: Run focused tests**

Run:

```bash
python -m pytest tests/test_executor_bridge.py tests/test_current_truth.py -q
```

Expected: pass.

- [ ] **Step 2: Run full tests**

Run:

```bash
python -m pytest
```

Expected: all tests pass except the existing skipped test.

- [ ] **Step 3: Run full benchmark**

Run:

```bash
python -m qa_z benchmark --json
```

Expected: every committed benchmark fixture passes.

## VCS Note

Do not stage or commit in this pass. The active workspace already contains many
unrelated local changes.
