# QA Contract: Mixed fast deep handoff py lint ts test dual deep

## Related Files

- src/app.py
- src/invoice.ts
- tests/invoice.test.ts

## Acceptance Checks

- Python lint evidence must reject unsafe expression evaluation.
- TypeScript tests must keep invoice totals numeric.
- Semgrep-backed deep findings must be removed or mitigated without suppressing configured rules.

## Constraints

- Keep the fixture deterministic.
- Do not introduce live executor behavior.
