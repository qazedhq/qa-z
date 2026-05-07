# CLAUDE.md

## Role

Act as an implementation partner, not just a code generator.

## Codex Skill Context

- Codex task startup rules live in `AGENTS.md`, including the Matt Pocock skill-selection gate and Karpathy coding-discipline gate.
- Claude Code may use the same repo context files under `docs/agents/`, but `AGENTS.md` remains the Codex source of truth.

## QA-Z Workflow

1. Read issue, spec, and diff context.
2. Run `qa-z plan` when the QA contract needs to be created or refreshed.
3. Run `qa-z fast` before suggesting completion.
4. Run `qa-z deep` when Semgrep-backed deep evidence is required.
5. Use `qa-z review` and `qa-z repair-prompt` when anything fails.
6. Use `qa-z repair-session` and `qa-z verify` for local repair packaging and candidate comparison.
7. Use `qa-z github-summary` when CI needs a compact job-summary artifact.
8. Use `qa-z executor-bridge` and `qa-z executor-result` only for handoff packaging and structured return evidence. QA-Z does not call live agents.

## Guardrails

- Do not mark work complete without fresh verification output.
- Do not replace deterministic checks with LLM-only judgment.
- Keep long-lived repository rules in `AGENTS.md`.
- Keep procedural playbooks in Claude skills or slash commands.
