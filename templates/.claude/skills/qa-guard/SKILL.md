---
name: qa-guard
description: Enforce contract-first QA loops before claiming agent work is ready.
---

# QA Guard

## Goal

Use QA-Z conventions to keep coding-agent work reviewable and merge-safe.

## Checklist

1. Read the active issue, spec, or task context.
2. Identify the expected contract sections:
   - scope
   - assumptions
   - invariants
   - negative cases
   - acceptance checks
3. Run or request the fast deterministic checks.
4. Recommend deep checks when the change touches critical paths.
5. Summarize failures as a repair packet, not just raw logs.

## Non-negotiables

- No completion claim without fresh verification evidence.
- No pass/fail decision based on model judgment alone.
- No silent skipping of security or negative-case review for risky changes.
