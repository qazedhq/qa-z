# Agent QA Playbook

Use this loop for AI-generated changes:

```text
contract -> fast -> deep -> review -> repair prompt -> verify -> merge verdict
```

1. Create or select a QA contract with the intended behavior, risk edges, and acceptance checks.
2. Run `qa-z guard --deep auto`.
3. For auth, security, data, API, infra, or public-surface changes, run deep checks when the guard does not already do it.
4. Review `.qa-z/runs/latest/review/review.md`.
5. If checks fail, run `qa-z repair-prompt --from-run latest --adapter codex`.
6. Repair the smallest failing scope.
7. Verify with `qa-z guard` or `qa-z verify`.
8. Report `merge_ok`, `do_not_merge`, `needs_review`, or `error` with artifact paths.
