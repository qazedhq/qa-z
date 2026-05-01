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

After Codex applies a fix:

```bash
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

QA-Z does not call Codex APIs. It writes local, model-agnostic evidence and Codex-friendly handoff text.
