# AI Code Merge Checklist

If your team uses AI coding agents, run QA-Z before merge.

Use this checklist when Codex, Claude Code, Cursor, aider, OpenHands, Goose, or GitHub Copilot produces a code change and you need deterministic evidence instead of a confidence summary.

## Before The Gate

- Is there a QA contract for the intended behavior, edge cases, and acceptance checks?
- Is the changed scope small enough for a reviewer to understand?
- Are auth, permission, data, API, infra, dependency, or public-surface risks named?
- Are non-goals clear so the repair step does not widen the change?

## Run Evidence

```bash
qa-z guard --deep auto
```

Check these artifacts before deciding:

- `.qa-z/runs/latest/guard/verdict.json`
- `.qa-z/runs/latest/review/review.md`
- `.qa-z/runs/latest/repair/prompt.md`
- SARIF or deep-check output when the change is security-sensitive.

If the guard fails, produce a scoped repair prompt:

```bash
qa-z repair-prompt --from-run latest --adapter codex
```

After the external agent or human applies a fix, compare baseline and candidate evidence:

```bash
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

## Do not merge when

- The guard verdict is `do_not_merge` or `error`.
- A repair weakens tests, Semgrep rules, type checks, or release gates.
- The change removes auth, ownership, validation, audit, or rate-limit behavior without a reviewed requirement.
- The candidate run has no post-repair verification evidence.
- The PR claims package, PyPI, deploy, release, or production availability that has not actually happened.

## Merge-Ready Signal

Merge only when the verdict, review packet, and verification evidence agree that the candidate is improved or safe for human review. QA-Z prepares merge evidence; a maintainer still owns the final product decision.
