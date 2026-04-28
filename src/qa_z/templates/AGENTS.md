# AGENTS.md

## Mission

Use QA-Z as the repository's quality control plane for agentic coding work.

## Review Guidelines

- Treat security regressions and missing authorization checks as P1.
- Treat broken migrations, destructive data changes, and missing rollback paths as P1.
- Treat contract mismatches between issue intent, implementation, and tests as P1.
- Prefer deterministic evidence from tests, typechecks, and scanners over stylistic opinions.
- If a change lacks negative-case coverage, call it out.

## QA-Z Workflow

- Use `qa-z plan` to create or refresh the QA contract when issue, spec, or diff context changes.
- Use `qa-z fast` for deterministic Python and TypeScript subprocess checks.
- Use `qa-z deep` for the configured Semgrep-backed deep pass when risk or policy requires it.
- Use `qa-z review` and `qa-z repair-prompt` to turn local artifacts into review and repair evidence.
- Use `qa-z repair-session` and `qa-z verify` to package a local repair workflow and compare candidate evidence.
- Use `qa-z github-summary` to publish local run evidence into CI job summaries.
- Use `qa-z executor-bridge` and `qa-z executor-result` only as live-free handoff and return contracts. QA-Z does not call live agents.

## Working Rules

- Keep recurring repository rules here.
- Put task-specific procedures in skills or command docs.
- Update this file whenever quality gates change.
- Keep instructions close to the code they govern when subtrees need tighter review.
