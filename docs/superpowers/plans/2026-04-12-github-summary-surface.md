# GitHub Summary Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make QA-Z fast results readable inside GitHub Actions while preserving downloadable review and repair artifacts.

**Architecture:** Keep deterministic fast artifacts as the source of truth. Add a small latest-run manifest writer/resolver, add file output support to review, and add a dedicated GitHub summary reporter plus CLI command for compact Markdown intended for `$GITHUB_STEP_SUMMARY`.

**Tech Stack:** Python `argparse`, dataclasses already in `qa_z.runners.models`, pytest, GitHub Actions YAML.

---

### Task 1: Stable Latest Run Manifest

**Files:**
- Modify: `src/qa_z/artifacts.py`
- Modify: `src/qa_z/reporters/run_summary.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
def test_fast_writes_latest_run_manifest(tmp_path, capsys):
    checks = [{"id": "py_test", "kind": "test", "run": python_command("")}]
    write_fast_config(tmp_path, checks)
    write_contract(tmp_path)
    output_dir = tmp_path / ".qa-z" / "runs" / "ci"

    exit_code = main([
        "fast",
        "--path",
        str(tmp_path),
        "--output-dir",
        str(output_dir),
        "--json",
    ])

    manifest = json.loads((tmp_path / ".qa-z" / "runs" / "latest-run.json").read_text(encoding="utf-8"))
    assert exit_code == 0
    assert manifest == {"run_dir": ".qa-z/runs/ci"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py::test_fast_writes_latest_run_manifest -q`
Expected: FAIL because `latest-run.json` is not written.

- [ ] **Step 3: Implement the manifest writer and resolver**

Add `write_latest_run_manifest(root, run_dir)` and make `resolve_latest_run_source()` prefer `.qa-z/runs/latest-run.json` when it points at a run containing `fast/summary.json`. Keep the existing mtime scan as a fallback.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py::test_fast_writes_latest_run_manifest -q`
Expected: PASS.

### Task 2: Review Output Directory

**Files:**
- Modify: `src/qa_z/reporters/review_packet.py`
- Modify: `src/qa_z/cli.py`
- Test: `tests/test_repair_prompt.py`

- [ ] **Step 1: Write the failing test**

```python
def test_review_from_run_writes_output_dir(tmp_path, capsys):
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    output_dir = tmp_path / ".qa-z" / "runs" / "2026-04-11T17-38-52Z" / "review"

    exit_code = main([
        "review",
        "--path",
        str(tmp_path),
        "--from-run",
        "latest",
        "--output-dir",
        str(output_dir),
    ])

    assert exit_code == 0
    assert (output_dir / "review.md").exists()
    assert "# QA-Z Review Packet" in (output_dir / "review.md").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_repair_prompt.py::test_review_from_run_writes_output_dir -q`
Expected: FAIL because `review` does not accept `--output-dir`.

- [ ] **Step 3: Implement output writing**

Add `write_review_artifacts(markdown, json_text, output_dir)` and use it when `review --output-dir` is provided. Write `review.md`; write `review.json` when `--json` is used or for run-aware packets where JSON is available.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_repair_prompt.py::test_review_from_run_writes_output_dir -q`
Expected: PASS.

### Task 3: GitHub Summary Reporter

**Files:**
- Create: `src/qa_z/reporters/github_summary.py`
- Modify: `src/qa_z/cli.py`
- Test: `tests/test_github_summary.py`

- [ ] **Step 1: Write failing reporter and CLI tests**

```python
def test_github_summary_renders_compact_failed_run():
    markdown = render_github_summary(summary, run_source, root=Path("/repo"))
    assert "# QA-Z Fast Summary" in markdown
    assert "**Status:** failed" in markdown
    assert "`py_test` - targeted - tests failed" in markdown
```

```python
def test_github_summary_cli_writes_output_file(tmp_path, capsys):
    write_config(tmp_path)
    write_contract(tmp_path)
    write_summary(tmp_path, "2026-04-11T17-38-52Z")
    output = tmp_path / ".qa-z" / "runs" / "ci" / "github-summary.md"

    exit_code = main(["github-summary", "--path", str(tmp_path), "--from-run", "latest", "--output", str(output)])

    assert exit_code == 0
    assert output.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_github_summary.py -q`
Expected: FAIL because the module and command do not exist.

- [ ] **Step 3: Implement compact Markdown rendering**

Render status, selection mode, totals, failed checks, changed files, selection groups, review artifact path, repair prompt path, and source summary path. Avoid raw failure dumps.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_github_summary.py -q`
Expected: PASS.

### Task 4: GitHub Actions Surface

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `templates/.github/workflows/vibeqa.yml`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Add tests for parser command registration**

Extend the parser test to require `github-summary`.

- [ ] **Step 2: Update workflows**

Capture the fast exit code, generate review, repair, and GitHub summary artifacts under the run directory, append summary Markdown to `$GITHUB_STEP_SUMMARY`, upload `.qa-z/runs`, then exit with the original fast code.

- [ ] **Step 3: Run CLI tests**

Run: `python -m pytest tests/test_cli.py tests/test_repair_prompt.py tests/test_github_summary.py -q`
Expected: PASS.

### Task 5: Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/artifact-schema-v1.md`
- Modify: `docs/mvp-issues.md`
- Modify: `qa-z.yaml.example` only if config surface changes

- [ ] **Step 1: Update README**

Document `github-summary`, `review --output-dir`, `latest-run.json`, and the CI behavior. Keep exclusions honest: no SARIF or PR annotations.

- [ ] **Step 2: Update artifact schema docs**

Document `latest-run.json`, `review/review.md`, `review/review.json`, `repair/prompt.md`, `repair/packet.json`, and `github-summary.md`.

- [ ] **Step 3: Run all tests**

Run: `python -m pytest`
Expected: PASS.
