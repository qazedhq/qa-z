# QA-Z Merge Safety

Use QA-Z evidence before saying an AI-generated change is safe.

- Do not claim code is safe without evidence.
- Summarize changes, risks, and affected files.
- Run or request `qa-z guard`.
- Escalate to deep checks for auth, security, data, API, infra, or public-surface changes.
- When checks fail, use `qa-z repair-prompt --from-run latest --adapter claude`.
- Verify the repaired run before saying it improved.
- Keep edits focused and avoid unrelated cleanup.
- End with a merge verdict and artifact paths.
