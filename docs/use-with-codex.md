# Use QA-Z With Codex

Use Codex to change code. Use QA-Z to decide whether the change is safe to merge.

## Loop

```bash
qa-z plan --diff changes.diff --title "Review Codex change" --slug codex-change --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Then give Codex the generated repair prompt:

```text
Fix the QA-Z repair packet at .qa-z/runs/baseline/repair/codex.md.
Preserve deterministic checks. Do not replace failures with LLM-only judgment.
After editing, rerun the validation commands listed in the packet.
```

Use `.qa-z/runs/latest/repair/codex.md` when you are following the latest QA-Z
run. Use a specific run path such as `.qa-z/runs/baseline/repair/codex.md` when
documenting a reproducible walkthrough.

## Copy This Prompt To Codex

Use this after QA-Z has generated a repair prompt.

```text
Read the QA-Z repair prompt at `.qa-z/runs/latest/repair/codex.md`.

Use QA-Z artifacts as the source of truth:
- `.qa-z/runs/latest/fast/summary.json`
- `.qa-z/runs/latest/deep/summary.json`
- `.qa-z/runs/latest/repair/codex.md`

Fix only the evidence-backed issues in the repair prompt.
Do not replace failing checks with LLM-only judgment.
Do not remove tests, weaken assertions, or hide Semgrep findings.
After editing, run the validation commands listed in the QA-Z repair prompt.
Then produce a short summary of changed files, validation results, and remaining risks.
```

QA-Z artifacts are the source of truth. Codex is the executor, not the judge.
QA-Z does not call Codex APIs. This snippet is a handoff prompt for a
human-operated Codex workflow.

After Codex applies a fix:

```bash
qa-z verify --from-run .qa-z/runs/baseline
```

QA-Z does not call Codex APIs. It writes local, model-agnostic evidence and Codex-friendly handoff text.
