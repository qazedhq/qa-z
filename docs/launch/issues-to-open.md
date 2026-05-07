# Issues To Open

## Add Published Demo GIF

Labels: docs, demo

Acceptance criteria:

- `docs/assets/qa-z-demo.gif` exists.
- README renders it near the top.
- The demo matches `qa-z demo auth-bug`.

## Harden Guard Replay

Labels: cli, guard

Acceptance criteria:

- `qa-z guard --from-run PATH` reuses existing artifacts.
- Tests cover replay and failure semantics.

## Expand Deep Risk Policies

Labels: deep, security

Acceptance criteria:

- Auth/security/data/API/infra changes map to explicit deep policy.
- Docs explain missing-tool behavior.
