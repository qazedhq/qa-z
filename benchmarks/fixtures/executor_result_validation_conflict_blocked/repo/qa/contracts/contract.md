# QA Contract: Executor result partial mixed verify fixture

## Related Files

- src/app.py
- src/invoice.ts

## Acceptance Checks

- The Python test failure should be repairable without regressing TypeScript.
- Partial completion must be reported conservatively until the regression is resolved.
