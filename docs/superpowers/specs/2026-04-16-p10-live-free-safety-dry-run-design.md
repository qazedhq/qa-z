# P10 Live-Free Safety Dry-Run And Multi-Result History Design

## Goal

Extend QA-Z's external-executor return path so one repair session can preserve a deterministic history of readable executor attempts, then evaluate that history through an explicit live-free safety dry-run command.

## Why This Slice

P9 froze the pre-live safety package, but QA-Z still reasons mostly from one latest executor result at a time.

That leaves two practical gaps:

1. repeated partial, no-op, stale, or rejected attempts are hard to inspect as one story
2. the safety package exists, but there is no explicit local command that reads real attempt history and explains where manual attention is now required

P10 closes those gaps without adding live execution, retry automation, or remote orchestration.

## Locked Decisions

- history is session-scoped, not bridge-scoped or loop-scoped
- every readable executor result attempt should be preserved when the owning session can be resolved, including accepted, partial, no-op, and rejected outcomes
- the safety evaluation is an explicit command, not an automatic side effect of ingest
- the default dry-run input is the whole session history plus its latest attempt

## Non-Goals

P10 does not add:

- live Codex or Claude execution
- automatic retries, redispatch, or scheduling
- mutation of repository code during dry-run
- LLM-only safety decisions
- replacement of the existing `executor-result ingest` contract

## Recommended Shape

### 1. Session-Local Attempt History

Each repair session gains a deterministic executor-results area:

```text
.qa-z/sessions/<session-id>/executor_results/
  history.json
  attempts/
    <attempt-id>.json
```

`attempts/<attempt-id>.json` stores the readable `qa_z.executor_result` payload exactly as QA-Z ingested it.

`history.json` stores the append-only machine-readable chronology for the session. Each attempt record should include:

- `attempt_id`
- `recorded_at`
- `bridge_id`
- `source_loop_id`
- `result_status`
- `ingest_status`
- `verify_resume_status`
- `verification_hint`
- `verification_triggered`
- `verification_verdict`
- `validation_status`
- `warning_ids`
- `backlog_categories`
- `changed_files_count`
- `notes_count`
- `attempt_path`
- `ingest_artifact_path`
- `ingest_report_path`

For backward compatibility, `executor_result.json` remains the session's latest accepted result artifact. The new history is additive.

### 2. Ingest Recording Rule

`executor-result ingest` keeps its current verdict logic, but once a readable result has been parsed and the owning session is available, QA-Z should append an attempt record to session history before returning success or a structured rejection.

That means accepted and rejected readable attempts both become visible in one chronology, as long as QA-Z can resolve the session directory.

If the session cannot be loaded at all, QA-Z keeps the current ingest rejection behavior and does not invent orphan session history.

### 3. Explicit Dry-Run Command

Add:

```text
qa-z executor-result dry-run --session <session>
```

This command reads:

- the session manifest
- the session-local safety package
- the session executor-result history
- the latest attempt in that history

It then writes a local safety audit, for example:

```text
.qa-z/sessions/<session-id>/executor_results/dry_run_summary.json
.qa-z/sessions/<session-id>/executor_results/dry_run_report.md
```

The command does not modify code, does not rerun verification, and does not auto-retry an executor. It is a deterministic operator-facing audit.

### 4. Dry-Run Evaluation Model

Dry-run should evaluate the frozen P9 safety rules against history evidence, not against hypotheticals.

Recommended top-level summary fields:

- `kind`: `qa_z.executor_result_dry_run`
- `schema_version`
- `session_id`
- `history_path`
- `safety_package_id`
- `evaluated_attempt_count`
- `latest_attempt_id`
- `latest_result_status`
- `latest_ingest_status`
- `verdict`
- `history_signals`
- `rule_evaluations`
- `next_recommendation`
- `report_path`

Recommended verdicts:

- `clear`: no current safety concern is visible in the session history
- `attention_required`: manual review is required before another external attempt should be treated as routine
- `blocked`: the latest or repeated history indicates a stronger stop condition, such as scope drift or completed-without-verification confidence

Recommended history signals:

- repeated partial attempts
- repeated rejected attempts
- repeated no-op or not-applicable attempts
- completed results blocked by verify-resume rules
- scope validation failures
- validation-consistency conflicts

### 5. Rule Evaluation Guidance

The dry-run should translate current evidence into explicit rule status:

- `no_op_requires_explanation`
  - attention when history contains no-op or not-applicable attempts without explanation warnings
- `retry_boundary_is_manual`
  - attention when repeated attempts show a pattern that should not be treated as routine silent retry
- `mutation_scope_limited`
  - blocked when history contains scope validation failure
- `unrelated_refactors_prohibited`
  - attention only when observed evidence suggests scope broadening; otherwise remain neutral instead of inventing claims
- `verification_required_for_completed`
  - blocked when completed attempts remain verify-blocked or produce mixed/regressed verification
- `outcome_classification_must_be_honest`
  - attention when completed attempts conflict with changed-files or validation evidence

The dry-run is not a second ingest engine. It is a deterministic reading of already-recorded evidence.

### 6. Backlog Resonance

Multi-result history should not remain invisible to self-improvement.

Self-inspection should read session executor-result histories and promote deterministic candidates when it sees patterns such as:

- repeated partial attempts -> `partial_completion_gap`
- repeated no-op attempts -> `no_op_safeguard_gap`
- repeated stale/mismatch/invalid attempts -> `workflow_gap`
- completed attempts that still stay verify-blocked -> `workflow_gap`

This keeps the "history echo" visible in backlog selection without requiring the dry-run command to have been executed.

## Compatibility

P10 should preserve current behavior for:

- single-result ingest
- latest session `executor_result.json`
- bridge/result contracts
- session verification flow

For sessions created before P10, dry-run and history reads should tolerate missing history by backfilling a single-attempt history from the latest stored session executor result when enough local data exists. If no result exists, the history remains empty and dry-run should say so clearly.

## Testing

P10 should add focused tests for:

- history append on accepted result ingest
- history append on readable rejected result ingest when the session is available
- stable history schema and attempt ordering
- dry-run clear, attention-required, and blocked outcomes
- backward-compatible history backfill for older sessions
- self-inspection promotion from repeated session attempt patterns
- CLI output for `executor-result dry-run`

## Success Criteria

P10 is complete when:

- QA-Z preserves readable executor attempt history per session
- the history includes both accepted and rejected readable attempts when the session exists
- `qa-z executor-result dry-run --session <session>` writes deterministic safety audit artifacts
- self-inspection can notice repeated executor attempt patterns from session history
- all current validation gates still pass
