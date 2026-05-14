---
name: project-improvement-loop
description: Use for broad, cross-project, quality, readiness, or "improve this project" requests. Converts broad requests into validated product slices.
---

# Project Improvement Loop

## Trigger
Use this skill when the request is broad, cross-project, quality/readiness oriented, or the next slice is unclear.

## Role Execution Policy
- If the user explicitly asks for subagents, parallel agents, delegation, or focused workers, dispatch the relevant `.codex/agents/*.toml` roles.
- Otherwise run the same roles inline in this order:
  1. product-flow-auditor pass
  2. implementation-surgeon pass
  3. verification-runner pass
  4. docs-truth-syncer pass
- In inline mode, do not pretend that separate agents ran.

## Steps
1. Confirm repository identity and dirty boundary.
2. Read AGENTS.md plus the docs hub.
3. If `docs/agent/next-real-slices.md` exists, use it as the default candidate queue; otherwise select one user-facing or release-blocking flow from repo evidence.
4. Run a product-flow-auditor pass, inline by default or as a subagent only when explicitly requested.
5. Pick the slice with the best impact, risk, and validation ratio.
6. Implement the selected slice through an implementation-surgeon pass.
7. Validate through a verification-runner pass.
8. Sync changed truth through a docs-truth-syncer pass.
9. Append one ledger entry to `docs/agent/work-slice-ledger.md`.
10. If the operating model already validates, switch to `product-code-slice` for the next iteration instead of adding more scaffold.
11. Continue to the next safe slice until blocked, no safe improvement remains, or the task budget ends.

## Do Not
- Do not spend the loop only updating reports.
- Do not weaken gates.
- Do not close external blockers locally.
- Do not ask for confirmation if a safe local slice exists.


## Product-Code Handoff
When the operating model is already present, the next improvement must be a code, test, runtime, capture, or evidence-tooling slice unless unsafe. Use `docs/agent/next-real-slices.md` and `$product-code-slice`.
