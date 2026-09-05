# Use QA-Z With Goose

Goose can help produce or repair code. QA-Z gives the reviewer a local guard, repair prompt, and verification loop before merge.

## Loop

Run the guard on the Goose-assisted change:

```bash
qa-z guard --deep auto
```

If the guard fails, produce the local repair prompt:

```bash
qa-z repair-prompt --from-run latest --adapter codex
```

Give Goose the repair brief:

```text
Use .qa-z/runs/latest/repair/prompt.md as the repair brief.
Fix only the evidence-backed failures.
Preserve the listed checks instead of replacing failures with confidence text.
```

After Goose or a human applies the repair, compare baseline and candidate evidence:

```bash
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

QA-Z does not call the agent, edit code, create branches, commit, push, or post GitHub comments.
