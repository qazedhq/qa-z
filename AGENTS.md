# AGENTS.md

## Repository Identity
- Product: QA-Z.
- Runtime: local deterministic QA control plane for coding-agent workflows.
- Critical user flows: diff/input, fast/deep analysis, SARIF/summary, guard decision, repair prompt, external executor handoff, benchmark proof.
- Release state: alpha. QA-Z must not be treated as an autonomous coding agent.

## Non-Negotiable Boundaries
- Do not directly fix target repositories as QA-Z improvement.
- Do not add hidden network, live model, branch mutation, commit, push, deployment, or GitHub bot-comment behavior.
- Do not weaken deterministic checks, benchmark expectations, release gates, artifact contracts, or validation criteria to pass.
- Do not overwrite unrelated dirty work.

## Startup Routing
1. Confirm this is `F:\JustTyping` and check dirty state.
2. Read this file plus `README.md`, `docs/product/PRODUCT_DIRECTION.md`, and `docs/agent/agent-operating-manual.md`, and `docs/agent/next-real-slices.md`.
3. Pick one QA evidence or release-blocking flow.
4. Use `.agents/skills/project-improvement-loop/SKILL.md` for broad improvement requests, then `.agents/skills/product-code-slice/SKILL.md` once the operating model is already present.
5. Implement the smallest safe Flow, Contract, Evidence, or Cleanup Slice.
6. Validate with the narrowest relevant command and report exact evidence.

## Slice Card
- Lane:
- User-facing flow:
- Slice type:
- User-visible outcome:
- Root cause:
- Files likely touched:
- Validation:
- Evidence:
- Stop rule:

## Project Priority Flows
1. Diff/input -> fast/deep analysis -> SARIF/summary -> github-summary -> guard decision.
2. Finding -> repair prompt -> external executor handoff -> verify.
3. Benchmark fixture -> risk policy -> regression proof.
4. Current-truth docs -> stale roadmap/select-next prevention.

## Codex-Native Operating Assets
- Primary: `.codex/agents/*.toml`, `.agents/skills/*/SKILL.md`, `docs/agent/*.md`.
- Compatibility mirror: `.claude/**`. Do not treat it as the Codex source of truth.
- Full pre-V3 root instructions are archived at `docs/agent/root-agents-before-v3.md`.

## Completion Rule
A task is complete only when code, runtime, test, validation, or docs truth moved and fresh evidence is reported. Operating-model or scaffold edits alone do not count as product improvement. External blockers stay blocked, and the next safe local slice must be named.
