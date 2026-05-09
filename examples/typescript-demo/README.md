# QA-Z TypeScript Demo

This demo is a small Vitest project for the TypeScript fast gate.

It is a fast-only demo, not a Next.js demo. It does not configure TypeScript-specific deep automation, does not call live agents, and does not run `executor-bridge` or `executor-result`.

## Visual proof

For the public launch terminal proof, see [qa-z-demo.svg](../../docs/assets/qa-z-demo.svg) and [qa-z-agent-auth-bug.cast](../../docs/assets/qa-z-agent-auth-bug.cast). This TypeScript demo remains a runnable fast-gate example; the deep `qa-z verify` proof is covered by the agent-auth-bug casts.

```bash
npm install
python -m qa_z plan --path . --title "Protect invoice totals" --issue issue.md --spec spec.md
python -m qa_z fast --path . --selection smart
```

The `qa-z.yaml` file wires the first TypeScript check set:

- `ts_lint` with ESLint
- `ts_type` with `tsc --noEmit`
- `ts_test` with `vitest run`
