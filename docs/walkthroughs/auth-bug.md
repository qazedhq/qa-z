# Walkthrough: AI Auth Bug Caught By QA-Z

This walkthrough uses [../../examples/agent-auth-bug/](../../examples/agent-auth-bug/).

```bash
qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
cp app/auth.fixed.py app/auth.py
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Expected: baseline fails, candidate passes, verification verdict is `improved`.
