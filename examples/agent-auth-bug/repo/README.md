# Agent Auth Bug Demo Repo

This directory contains the small repository payload used by the auth-bug demo
story. The top-level `examples/agent-auth-bug` directory remains the executable
demo workspace for `qa-z demo auth-bug`; this nested repo mirror keeps the
copy-paste example layout explicit for readers.

Story:

- An AI agent weakened invoice authorization.
- `pytest` catches the non-owner access regression.
- Semgrep flags the signed-in-user shortcut and the missing invoice owner comparison.
- QA-Z turns the deterministic evidence into a repair prompt and merge verdict.

Run from this directory:

```bash
qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z guard --title "AI auth bug caught by QA-Z" --slug ai-auth-bug --deep never
```
