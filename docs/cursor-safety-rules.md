# Cursor Safety Rules

Install the QA-Z Cursor rule:

```bash
qa-z skill install cursor
```

Cursor should:

- avoid unrelated refactors
- run or request `qa-z guard`
- use deep checks for risky surfaces
- generate a repair prompt when checks fail
- verify repairs before saying the change improved
