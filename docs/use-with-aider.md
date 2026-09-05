# Use QA-Z With aider

aider can edit a repository quickly. QA-Z gives the maintainer local merge evidence before the change lands.

## Loop

Run QA-Z after the aider change is available in the working tree:

```bash
qa-z guard --deep auto
```

If the guard fails, generate a scoped repair brief:

```bash
qa-z repair-prompt --from-run latest --adapter codex
```

Give aider the local repair prompt:

```text
Use .qa-z/runs/latest/repair/prompt.md as the repair brief.
Fix only the evidence-backed failures.
Keep deterministic checks and validation commands intact.
```

After aider applies the repair, compare the baseline and candidate runs:

```bash
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

QA-Z does not call the agent, edit code, create branches, commit, push, or post GitHub comments.
