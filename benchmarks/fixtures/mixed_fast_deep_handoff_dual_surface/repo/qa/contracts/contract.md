# QA Contract: Mixed fast deep handoff dual surface

## Related Files

- src/app.py
- src/invoice.ts

## Acceptance Checks

- Python tests must reject unsafe expression evaluation.
- TypeScript invoice totals must remain typed as numbers.
- Semgrep-backed deep findings must be removed or mitigated without suppressing configured rules.

## Constraints

- Keep the fixture deterministic.
- Do not introduce live executor behavior.
