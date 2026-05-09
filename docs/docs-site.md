# Docs Site Plan

The official docs site should make QA-Z easier to adopt without turning the repository README back into a manual.

## First Navigation

- Quickstart.
- Five-minute demo, backed by the static hosted demo plan in `docs/hosted-demo.md`.
- GitHub Action.
- Use with Codex.
- Use with Claude Code.
- Use with Cursor.
- Use with Semgrep.
- Artifact reference.
- Public roadmap.

## Hosted Demo Boundary

The docs site can include a hosted demo page, but it should remain static: embed the recorded cast, link to `examples/agent-auth-bug`, and show the replay commands and generated `.qa-z/runs/*` artifacts. It must not describe QA-Z Cloud, live-agent execution, or any hidden hosted backend.

## Build Boundary

The docs site remains future scope until the repository has a stable static-site tool choice. Until then, Markdown under `docs/` is the canonical source.
