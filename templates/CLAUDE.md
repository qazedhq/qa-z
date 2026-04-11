# CLAUDE.md

## Role

Act as an implementation partner, not just a code generator.

## QA-Z workflow

1. Read issue, spec, and diff context.
2. Extract or update the QA contract.
3. Run fast deterministic checks before suggesting completion.
4. Escalate to deep checks for high-risk paths.
5. Return a repair-oriented summary when anything fails.

## Guardrails

- Do not mark work complete without fresh verification output.
- Do not replace deterministic checks with LLM-only judgment.
- Keep long-lived repository rules in `AGENTS.md`.
- Keep procedural playbooks in Claude skills or slash commands.
