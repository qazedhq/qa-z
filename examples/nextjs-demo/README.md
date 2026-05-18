# Next.js Demo

This is a runnable, minimal Next.js and TypeScript fast-gate demo for QA-Z.

The demo keeps the app small: `app/page.tsx` renders static invoice access
copy, while `src/invoice-access.ts` holds the deterministic logic covered by
Vitest. Tests do not start a browser, call the network, use hosted services, or
call external APIs.

## Run The Local Checks

```bash
npm install
npm run lint
npm run typecheck
npm test
```

## Run QA-Z

```bash
python -m qa_z plan --path . --title "Protect Next.js invoice access" --issue issue.md --spec spec.md
python -m qa_z fast --path . --selection smart
```

The `qa-z.yaml` file wires the deterministic TypeScript fast gate:

- `ts_lint` with `npm run lint`
- `ts_type` with `npm run typecheck`
- `ts_test` with `npm test`

QA-Z invokes those same package scripts through `scripts/npm-run.mjs` so the
configured subprocess works on Windows and POSIX shells.

Expected QA-Z runtime artifacts are local:

- `.qa-z/runs/latest`
- `.qa-z/runs/latest/fast/summary.json`
- review or repair artifacts only when you run the corresponding QA-Z commands

Generated `.qa-z/**` evidence remains local and must not be committed.
Generated `qa/contracts/**`, `node_modules/**`, `.next/**`, and coverage output
also stay out of source control unless a future fixture intentionally freezes a
small artifact with explicit review context.

## Boundaries

This demo has no live agents, no hosted services, no package publish, no executor-bridge/result behavior, no tag/release/deploy path, and no bot-comment automation. It does not claim broad Next.js-specific deep automation; deep checks remain empty unless a future deterministic local rule is added and tested.
