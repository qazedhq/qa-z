# P8-B Mixed-Surface Realism Expansion Design

## Goal

Expand QA-Z benchmark and verification coverage so the corpus models more realistic mixed-surface repository changes across Python, TypeScript, docs/schema maintenance, worktree cleanup, and executor-result ingest outcomes.

## Scope

P8-B stays local and deterministic. It adds or extends benchmark fixtures, narrow expectation parsing, verification summary fields, and documentation. It does not add live executor APIs, automatic code editing, remote orchestration, or a new benchmark contract family.

## Fixture Shapes

The expansion should cover these classes:

- cross-language repair tradeoffs where one language improves and another regresses
- functional fixes combined with worktree or integration cleanup
- docs/schema alignment work that should stay functionally `unchanged`
- executor-result ingest cases for `partial` and justified `no_op` returns
- cleanup-oriented work that improves operational safety without claiming functional improvement

## Contract Strategy

Keep `expect_fast`, `expect_deep`, `expect_handoff`, `expect_verify`, and `expect_executor_result` as the only top-level expectation sections. Add only narrow keys that increase realism without forking the schema:

- `resolved_count_min`
- `regression_count_min`
- `remaining_issue_count_min`
- `expected_recommendation`
- `expected_ingest_status`

Executor-result benchmark summaries may also expose additive list fields such as backlog implication categories and warning ids when that helps fixtures assert realistic downstream behavior.

## Verification Semantics

Verification must stay conservative:

- resolved plus regression remains `mixed`
- no-op or maintenance-only cases remain `unchanged` unless deterministic QA evidence improves
- partial executor results should not look better than the available verify evidence justifies
- cleanup-only work should be distinguishable from actual functional repair

## Non-Goals

- live Codex or Claude execution
- auto-editing code from benchmark runs
- remote queues, daemons, or schedulers
- broad redesign of benchmark result artifacts
- speculative maintenance scoring based on LLM judgment
