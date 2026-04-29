# QA-Z examples

Start here:

| Example | Status | What it shows |
| --- | --- | --- |
| [typescript-demo](typescript-demo/) | Runnable | ESLint, `tsc --noEmit`, and Vitest fast gate |
| [fastapi-demo](fastapi-demo/) | Runnable | Passing fast/review flow and intentional failing repair-prompt flow |
| [nextjs-demo](nextjs-demo/) | Placeholder-only | Planned future Next.js workflow boundary |

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
