# P8-C Executor-Result Freshness And Ingest Hardening Design

## Goal

Harden QA-Z's executor-result return path so freshness and ingest decisions stay conservative when external evidence is stale, future-dated, or internally inconsistent.

## Scope

P8-C stays local and deterministic. It extends the existing executor-result ingest path, benchmark runner, committed benchmark corpus, and docs. It does not add live executor APIs, auto-edit behavior, retry daemons, remote orchestration, or a new contract family.

## Hardening Targets

P8-C focuses on two narrow gaps:

- freshness should consider the ingest reference time, not only bridge and session timestamps
- validation metadata should not be trusted when its summary conflicts with the detailed per-command results

## Freshness Semantics

Executor-result freshness should reject impossible timestamp ordering:

- result before bridge: already invalid
- result older than a newer session: already stale
- result newer than the ingest reference time: new invalid freshness case

The ingest summary should record the ingest reference timestamp inside `freshness_check` so downstream tools and benchmark fixtures can inspect exactly what was compared.

## Validation Consistency Semantics

Completed results may still be stored when the artifact is structurally valid, but QA-Z should not resume verification if validation evidence is self-contradictory. Examples:

- `validation.status == passed` while a detailed result is `failed`
- `validation.status == failed` while all detailed results are `passed`
- a detailed validation result reports a command that was not declared in `validation.commands`

These cases should surface as explicit warnings, block automatic verify resume, and emit a structural backlog implication rather than looking like a clean completed repair.

## Benchmark Strategy

The benchmark corpus should cover both sides of the hardening:

- a rejected executor-result fixture with a future timestamp
- an accepted-with-warning fixture where validation evidence blocks verify resume

The benchmark runner should treat stored ingest rejections as first-class fixture outcomes so rejected cases can be asserted without looking like harness failures.

## Contract Strategy

Keep the existing benchmark sections:

- `expect_executor_result`
- `expect_verify`

Add only narrow executor-result actual fields when fixtures need them:

- `freshness_status`
- `freshness_reason`
- `provenance_status`
- `provenance_reason`

Existing additive aliases such as `expected_ingest_status` and `expected_recommendation` remain the preferred expectation shape.

## Non-Goals

- live Codex or Claude execution
- remote job queues, schedulers, or daemons
- automatic result replay or retry orchestration
- broad redesign of the executor-result schema
- LLM-only interpretation of freshness or validation quality
