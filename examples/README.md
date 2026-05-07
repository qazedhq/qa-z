# QA-Z examples

Start here:

| Example | Status | What it shows |
| --- | --- | --- |
| [agent-auth-bug](agent-auth-bug/) | Runnable | Five-minute "AI auth bug caught by QA-Z" repair-evidence demo |
| [fastapi-agent-bug](fastapi-agent-bug/) | Runnable | FastAPI auth check regression with fast, deep, repair, and verify evidence |
| [typescript-agent-bug](typescript-agent-bug/) | Runnable | TypeScript agent bug caught by local checks and a Semgrep rule |
| [typescript-demo](typescript-demo/) | Runnable | ESLint, `tsc --noEmit`, and Vitest fast gate |
| [fastapi-demo](fastapi-demo/) | Runnable | Passing fast/review flow and intentional failing repair-prompt flow |
| [nextjs-demo](nextjs-demo/) | Placeholder-only | Planned future Next.js workflow boundary |

## Agent Auth Bug

From `examples/agent-auth-bug/`:

```bash
qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

This run is expected to fail. It demonstrates the public safety-belt story: an AI-generated auth bug becomes deterministic repair evidence before merge.

## FastAPI Agent Bug

From `examples/fastapi-agent-bug/`:

```bash
qa-z plan --title "FastAPI auth check caught by QA-Z" --issue issue.md --spec spec.md --slug fastapi-agent-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Copy `app/main.fixed.py` over `app/main.py`, run the candidate fast and deep gates, then compare with `qa-z verify`.

## TypeScript Agent Bug

From `examples/typescript-agent-bug/`:

```bash
qa-z plan --title "TypeScript agent bug caught by QA-Z" --issue issue.md --spec spec.md --slug typescript-agent-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Copy `src/invoice.fixed.ts` over `src/invoice.ts`, run the candidate fast and deep gates, then compare with `qa-z verify`.

## TypeScript Fast Gate

From `examples/typescript-demo/`:

```bash
npm install
python -m qa_z plan --path . --title "Protect invoice totals" --issue issue.md --spec spec.md
python -m qa_z fast --path . --selection smart
```

This demo wires ESLint, TypeScript type checking, and Vitest through `qa-z.yaml`.

## FastAPI Repair Flow

From `examples/fastapi-demo/`:

```bash
python -m qa_z init --path .
python -m qa_z plan --path . --title "Protect invoice access" --issue issue.md --spec spec.md
python -m qa_z fast --path . --output-dir .qa-z/runs/pass
python -m qa_z review --path . --from-run .qa-z/runs/pass
python -m qa_z repair-prompt --path . --from-run .qa-z/runs/pass
```

To inspect an intentional failure packet:

```bash
python -m qa_z fast --path . --config qa-z.failing.yaml --output-dir .qa-z/runs/fail
python -m qa_z review --path . --from-run .qa-z/runs/fail
python -m qa_z repair-prompt --path . --from-run .qa-z/runs/fail
```

The failing run is expected. It exists to show deterministic repair evidence, not a broken demo.

## Next.js Placeholder

`examples/nextjs-demo/` is intentionally not runnable yet. It stays labeled as a placeholder until it contains its own package files, QA-Z config, source, tests, and deterministic expected commands.
