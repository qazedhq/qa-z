---
name: qa-z-merge-safety
description: Make AI-generated code safer to merge by requiring QA contracts, checks, repair prompts, and verification evidence.
---

# QA-Z Merge Safety Skill

## Goal

Make AI-generated changes safe to merge by turning them into deterministic evidence.

## When To Use

Use this skill for any coding-agent change, especially auth, security, data, API, infra, or public-surface work.

## Required Workflow

1. Establish or select a QA contract.
2. Run `qa-z guard` when available.
3. If using the long form, run `qa-z fast`, `qa-z deep --from-run latest` when risk warrants it, `qa-z review --from-run latest`, and `qa-z repair-prompt --from-run latest`.
4. Repair only the failing scope.
5. Verify the repaired run before reporting improvement.

## Forbidden Behavior

- Do not claim code is safe without evidence.
- Do not replace deterministic pass/fail checks with LLM-only judgment.
- Do not weaken tests, lint, type checks, Semgrep rules, or contracts to pass.
- Do not make unrelated refactors.
- Do not let QA-Z edit, commit, push, open PRs, or comment on GitHub as normal runtime behavior.

## Evidence Contract

Report the command run, exit status, changed risk area, merge verdict, and artifact paths under `.qa-z/runs/latest/`.

## QA-Z Command Sequence

```bash
qa-z guard --adapter codex --deep auto
qa-z repair-prompt --from-run latest --adapter codex
qa-z verify --from-run latest
```

## Repair Prompt Rules

Use the repair prompt as the repair scope. Fix blocking checks first and keep validation commands intact.

## Verification Rules

After repair, rerun the checks that failed and then the guard or verify command. Do not infer improvement from code review alone.

## Merge Verdict Rules

- `merge_ok`: deterministic guard evidence passed.
- `do_not_merge`: fast/deep checks failed or blocking findings remain.
- `needs_review`: checks are missing, skipped, or unsupported.
- `error`: QA-Z could not complete the evidence run.
