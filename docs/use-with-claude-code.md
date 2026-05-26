# Use QA-Z With Claude Code

Use Claude Code for implementation. Use QA-Z for the deterministic merge gate.

## Loop

```bash
qa-z plan --diff changes.diff --title "Review Claude Code change" --slug claude-change --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter claude
```

Then pass the generated Claude handoff into Claude Code:

```text
Use the QA-Z repair handoff at .qa-z/runs/baseline/repair/claude.md.
Fix only the evidence-backed failures and rerun the listed validation commands.
Do not add hidden network dependencies to local QA.
```

After Claude Code applies a repair, verify the candidate evidence:

```bash
qa-z verify --from-run .qa-z/runs/baseline
```

QA-Z keeps Claude-specific instructions in adapter output. The planner and runners remain model-agnostic.
