# TypeScript Agent Bug Demo

TypeScript agent bug: an agent changed invoice authorization so any signed-in user can read any invoice.

This demo is dependency-light. The QA-Z checks run local Node scripts so the example can be replayed without installing npm packages, while the source stays TypeScript-shaped.

## Baseline

```bash
qa-z plan --title "TypeScript agent bug caught by QA-Z" --issue issue.md --spec spec.md --slug typescript-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Expected: `ts_test` fails and the local Semgrep rule flags the unsafe signed-in-user shortcut.

## Candidate

```bash
cp src/invoice.fixed.ts src/invoice.ts
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

PowerShell:

```powershell
Copy-Item src\invoice.fixed.ts src\invoice.ts -Force
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```
