# QA-Z Merge Safety

Use QA-Z before calling AI-generated code safe to merge.

- Do not claim code is safe without evidence.
- Summarize changed behavior and merge risks.
- Run or request `qa-z guard` or at least `qa-z fast`.
- Run `qa-z deep --from-run latest` for auth, security, data, API, infra, or public-surface risk.
- Generate `qa-z repair-prompt --from-run latest --adapter codex` when checks fail.
- Verify repairs before saying the result improved.
- Avoid unrelated refactors.
- Report the merge verdict with artifact paths under `.qa-z/runs/latest/`.
