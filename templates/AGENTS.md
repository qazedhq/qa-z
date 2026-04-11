# AGENTS.md

## Mission

Use QA-Z as the repository's quality control plane for agentic coding work.

## Review guidelines

- Treat security regressions and missing authorization checks as P1.
- Treat broken migrations, destructive data changes, and missing rollback paths as P1.
- Treat contract mismatches between issue intent, implementation, and tests as P1.
- Prefer deterministic evidence from tests, typechecks, and scanners over stylistic opinions.
- If a change lacks negative-case coverage, call it out.

## Working rules

- Keep recurring repository rules here.
- Put task-specific procedures in skills or command docs.
- Update this file whenever quality gates change.
- Keep instructions close to the code they govern when subtrees need tighter review.
