# Use QA-Z With Cursor

Cursor can write and refactor code quickly. QA-Z gives the merge reviewer deterministic evidence before the change lands.

## Loop

```bash
qa-z plan --diff changes.diff --title "Review Cursor change" --slug cursor-change --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter handoff
```

Paste the repair target back into Cursor:

```text
Use .qa-z/runs/baseline/repair/prompt.md as the repair brief.
Fix the deterministic failures first.
Keep the validation commands unchanged unless the QA-Z config is intentionally updated.
```

Then run the candidate evidence:

```bash
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Cursor remains the editor. QA-Z remains the local QA evidence layer.
