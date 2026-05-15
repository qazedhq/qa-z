# Docs Site Plan

The official docs site should make QA-Z easier to adopt without turning the repository README back into a manual.

## First Navigation

- Quickstart.
- Five-minute demo.
- GitHub Action.
- Use with Codex.
- Use with Claude Code.
- Use with Cursor.
- Use with Semgrep.
- Artifact reference.
- Public roadmap.

## Build Boundary

The docs site remains future scope until the repository has a stable static-site tool choice. Until then, Markdown under `docs/` is the canonical source.

## Hosted Demo Page

The first hosted-demo page should be static and sourced from:

- `docs/hosted-demo.md`
- `docs/demo-script.md`
- `docs/assets/qa-z-agent-auth-bug.cast`
- `docs/assets/qa-z-demo.cast`
- `docs/assets/qa-z-demo.svg`

The docs site must not imply QA-Z Cloud, hidden backend state, live-agent execution, or uploaded source-code analysis. The page should link users back to local replay commands.
