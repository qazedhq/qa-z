# Codex Repair Recipes

## Failed Guard

```text
Use `.qa-z/runs/latest/repair/codex.md`.
Fix only the targets named by QA-Z.
Do not weaken tests or config.
Rerun `qa-z guard --adapter codex --deep auto`.
Report the new verdict and artifact paths.
```

## Deep Finding

```text
Inspect `.qa-z/runs/latest/deep/summary.json`.
Fix the blocking finding without suppressing the rule unless the contract permits it.
Rerun deep checks and guard.
```
