# Use QA-Z With OpenHands

OpenHands can drive an implementation workflow. QA-Z stays outside that executor and records deterministic evidence for the merge decision.

## Loop

Run QA-Z after the OpenHands-produced change is available locally:

```bash
qa-z guard --deep auto
```

If the guard fails, create a repair brief:

```bash
qa-z repair-prompt --from-run latest --adapter codex
```

Pass the repair prompt back to the external executor:

```text
Use .qa-z/runs/latest/repair/prompt.md as the repair brief.
Fix only the evidence-backed failures.
Do not widen the task beyond the listed files and validation commands.
```

After the repair, compare evidence:

```bash
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

QA-Z does not call the agent, edit code, create branches, commit, push, or post GitHub comments.
