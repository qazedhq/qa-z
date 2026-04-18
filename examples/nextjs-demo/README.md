# Next.js Demo

This is a placeholder-only directory for a future Next.js repository example.

This directory is not wired as a runnable demo yet and is not a runnable Next.js project. It does not include `package.json`, does not include `qa-z.yaml`, does not call live agents, and does not run `executor-bridge` or `executor-result`. For the landed TypeScript fast-check flow, use `examples/typescript-demo`.

Current QA-Z alpha support that a future Next.js demo should reuse:

- `qa-z plan` for issue, spec, and diff-backed contracts
- `qa-z fast` for ESLint, `tsc --noEmit`, and Vitest-style deterministic checks
- `qa-z deep` for configured Semgrep-backed findings, not TypeScript-specific deep automation
- `qa-z review`, `qa-z repair-prompt`, `qa-z repair-session`, and `qa-z verify` for artifact-driven repair loops

Keep this placeholder honest until the example contains its own package files,
QA-Z config, source, tests, and deterministic expected commands.
