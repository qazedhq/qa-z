# Agent Operating Manual

Use this folder for durable agent operating knowledge. Keep root `AGENTS.md` short and operational; move longer explanations, ledgers, and maps here.

## Required Loop
1. Confirm dirty state and active repository.
2. Choose one user-facing or release-blocking flow.
3. State the intended change and relevant verification briefly.
4. Dispatch subagents only when explicitly requested.
5. Run the narrowest meaningful validation first.
6. Update only truth surfaces that changed.
7. Update the ledger only when it prevents repeated work or records a changed release decision.

## Role Execution
- Work directly; separate simulated role passes are unnecessary.
- Dispatch actual subagents only when the user explicitly asks for subagents, delegation, parallel agents, or focused workers.
- In inline mode, do not claim separate agents ran.

## Archived Root Guidance
- The full pre-V3 root instruction file is preserved at `root-agents-before-v3.md`.
- Do not copy long workflow routing back into root `AGENTS.md`; keep root short and move durable detail here.

## Slice Types
- Flow Slice: improves a real screen, API, command, or user path.
- Contract Slice: hardens API, data, auth, provider, image, release, or validation contracts.
- Evidence Slice: makes an implemented behavior provable through commands, captures, reports, or artifacts.
- Cleanup Slice: removes repeated confusion, stale docs, or recurring workflow failures.


## Product-Code Handoff
Once the operating model files exist and validate, broad improvement requests should not keep editing this folder. Read `next-real-slices.md`, pick one local-safe slice, and move to product code, tests, runtime validation, capture tooling, or evidence tooling.

Operating-model edits are valid only when the validator fails, the user asks to change the workflow, or a recurring failure shows the workflow itself is misleading.
