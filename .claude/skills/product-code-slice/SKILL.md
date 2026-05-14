---
name: product-code-slice
description: Use after the agent operating model exists to select and execute one real product code/test/runtime slice instead of more scaffolding.
---

# Product Code Slice

## Trigger
Use this skill when `AGENTS.md`, `.codex/agents`, `.agents/skills`, and `docs/agent` are already present and the user asks to continue improving the project.

## Goal
Turn the operating model into one concrete code, test, runtime, capture, or validation improvement.

## Steps
1. Read `AGENTS.md`, `docs/agent/agent-operating-manual.md`, and `docs/agent/next-real-slices.md`.
2. Pick the highest-impact local-safe slice unless fresh repo evidence shows a more urgent P0.
3. Write a Slice Card before editing.
4. Touch product code, tests, runtime validation, or evidence tooling first. Update docs only if truth changed.
5. Run the narrowest meaningful validation.
6. Append `docs/agent/work-slice-ledger.md` with user impact, validation, blocker state, and next safe slice.

## Stop Rules
- Stop scaffolding the operating model unless validation says required files are missing or contradictory.
- Keep approval, credential, live deploy, external provider, device/manual, Play/public, or paid-service blockers blocked.
- Do not claim production/release readiness from a local code slice without the required evidence.
