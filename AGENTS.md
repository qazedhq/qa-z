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
1. Confirm repository identity, branch, and dirty state; a checkout may live outside `F:\JustTyping`.
2. Read only the contract needed for the task. Use `docs/product/PRODUCT_DIRECTION.md` for product scope and `docs/agent/next-real-slices.md` when no concrete task is given.
3. Choose a bounded change and the check that proves it. Explicit workflow and instruction cleanup requests are valid tasks.
4. Run the relevant check once per changed input. Expand verification after a failure or when release requirements demand it.
5. Report the change, verification result, and remaining blocker. Cards, simulated role passes, and fixed report templates are optional.

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
A task is complete when the requested change is implemented and relevant evidence is reported. Keep local checks, package publication, and external blockers distinct.
