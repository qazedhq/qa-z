# QA-Z Merge Safety

When reviewing or changing code, treat QA-Z artifacts as the merge-safety source of truth.

- Do not claim code is safe without evidence.
- Summarize behavior changes and risks.
- Prefer `qa-z guard`; otherwise request `qa-z fast` and `qa-z review`.
- Use deep checks for auth, security, data, API, infra, or public-surface changes.
- When checks fail, request `qa-z repair-prompt --from-run latest --adapter codex`.
- Verify repaired changes before saying the result improved.
- Avoid unrelated refactors.
- Report a merge verdict with artifact paths.
