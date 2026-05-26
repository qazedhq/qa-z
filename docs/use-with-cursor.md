# Use QA-Z With Cursor

Cursor can write and refactor code quickly. QA-Z gives the merge reviewer deterministic evidence before the change lands.

## Loop

```bash
qa-z plan --diff changes.diff --title "Review Cursor change" --slug cursor-change --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter cursor
```

Paste the repair target back into Cursor:

```text
Use .qa-z/runs/baseline/repair/cursor.md as the repair brief.
Fix only the evidence-backed files and risks.
Run the required validation commands and do not claim success without validation.
```

Then verify the candidate evidence:

```bash
qa-z verify --from-run .qa-z/runs/baseline
```

Cursor remains the editor. QA-Z remains the local QA evidence layer.
