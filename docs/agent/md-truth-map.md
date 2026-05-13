# Markdown Truth Map

## Source Of Truth
- Next executable slice queue: `docs/agent/next-real-slices.md` (candidate queue; verify before editing)
- Root operating rules: `AGENTS.md`
- Product context: `docs/product/PRODUCT_DIRECTION.md`
- Public entry point: `README.md`
- Current truth reports: current-state analysis, next-improvement roadmap, release docs, and benchmark evidence when present.
- Agent operating docs: `docs/agent/*.md`

## Freshness Rules
- Generated reports are evidence, not policy, unless a handoff explicitly promotes them.
- Handoff docs must include date, source branch or commit when available, validation command, and blocker state.
- Release claims require linked evidence. Without evidence, keep the claim candidate, partial, blocked, or no-go.
- Do not duplicate long runbooks in `AGENTS.md`; link the owner doc instead.

## Candidate Queue Rule
- Candidate queues are not evidence. They help choose the next code/test/runtime slice, but the repo state and validation output decide truth.
