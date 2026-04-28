# QA Contract: Mixed fast deep scan warning fast-only handoff

## Related Files

- src/app.py
- src/worker.py
- src/invoice.ts

## Acceptance Checks

- TypeScript invoice code must not carry lint failures.
- Semgrep scan-quality warnings must remain visible without becoming blocking deep findings.
- Repair handoff must stay focused on the blocking fast check when deep only reports warnings.

## Constraints

- Keep the fixture deterministic.
- Do not introduce live executor behavior.
