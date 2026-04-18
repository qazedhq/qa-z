---
name: qa-guard
description: Enforce contract-first QA loops before claiming agent work is ready.
---

# QA Guard

## Goal

Use QA-Z conventions to keep coding-agent work reviewable and merge-safe.

## Checklist

1. Read the active issue, spec, or task context.
2. Run `qa-z plan` when the QA contract needs to be created or refreshed.
3. Identify the expected contract sections:
   - scope
   - assumptions
   - invariants
   - negative cases
   - acceptance checks
4. Run or request `qa-z fast` for deterministic checks.
5. Run or request `qa-z deep` for configured Semgrep-backed checks when the change touches critical paths.
6. Use `qa-z review` and `qa-z repair-prompt` to summarize failures as repairable evidence, not raw logs.
7. Use `qa-z repair-session` and `qa-z verify` for local repair packaging and candidate comparison.
8. Use `qa-z executor-bridge` and `qa-z executor-result` only for live-free handoff and return evidence. QA-Z does not call live agents.

## Non-negotiables

- No completion claim without fresh verification evidence.
- No pass/fail decision based on model judgment alone.
- No silent skipping of security or negative-case review for risky changes.
