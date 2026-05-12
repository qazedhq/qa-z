# Subagent Roster

Use installed Codex role files under `.codex/agents/*.toml` as the source of truth. `.claude/agents/` is a compatibility mirror only. Actual subagent dispatch is only for sessions where the user explicitly asks for subagents or parallel agent work.

## Common Roles
- `product-flow-auditor`: read-only candidate-slice discovery.
- `implementation-surgeon`: one narrow implementation slice.
- `verification-runner`: targeted validation and failure summary.
- `docs-truth-syncer`: update only docs whose truth changed.

## QA-Z Specialist Lanes
- `qa-z-risk-model-auditor`: merge-safe/unsafe criteria and fixture coverage.
- `qa-evidence-surgeon`: evidence, fixture, and repair-handoff implementation without editing target repositories.
- `benchmark-fixture-builder`: focused fixtures that reproduce regressions.
- `repair-prompt-reviewer`: repair prompts that are executable and evidence-backed.
