# QA-Z Repair Sessions

Repair sessions are a light local workflow wrapper around existing QA-Z repair handoff and verification artifacts.

They are not live executor integration. They do not call Codex or Claude APIs, create queues, schedule jobs, commit code, push branches, or run remote workers. A session only records where the baseline evidence lives, prepares deterministic handoff material, waits for an external repair executor, and then verifies a candidate run.

## Workflow

Start with an existing baseline run:

```bash
python -m qa_z repair-session start --baseline-run .qa-z/runs/<baseline>
```

This creates:

```text
.qa-z/sessions/<session-id>/
  session.json
  executor_guide.md
  executor_safety.json
  executor_safety.md
  handoff/
    packet.json
    prompt.md
    handoff.json
    codex.md
    claude.md
  executor_results/
    history.json
    attempts/
      <attempt-id>.json
    dry_run_summary.json
    dry_run_report.md
```

The executor guide explains what the human or external coding agent should fix, where the handoff artifacts are, what not to change, and how to verify afterward. The paired `executor_safety.json` and `executor_safety.md` files freeze the pre-live safety boundary for that session so the same rules can be reused by bridge packaging later. The `executor_results/` subtree stays mostly empty until an external result is ingested or a live-free dry-run audit is written.

Check session state:

```bash
python -m qa_z repair-session status --session .qa-z/sessions/<session-id>
```

After code has been edited, verify the repair by creating a session-local candidate rerun:

```bash
python -m qa_z repair-session verify --session .qa-z/sessions/<session-id> --rerun
```

Or verify against an existing candidate run:

```bash
python -m qa_z repair-session verify --session .qa-z/sessions/<session-id> --candidate-run .qa-z/runs/<candidate>
```

Verification writes:

```text
.qa-z/sessions/<session-id>/
  candidate/        # only when --rerun uses the default output
  verify/
    summary.json
    compare.json
    report.md
  outcome.md
  summary.json
```

## States

The manifest state starts as `waiting_for_external_repair` once handoff artifacts and the executor guide are ready. A completed verification updates it to `completed`.

Reserved states for future recovery and diagnosis are:

- `created`
- `handoff_ready`
- `candidate_generated`
- `verification_complete`
- `failed`

## Outcome

The session summary records the verification verdict, blocking counts before and after repair, resolved issue count, new or regressed issue count, and a deterministic next recommendation:

- `improved`: merge candidate
- `mixed`: inspect regressions
- `regressed`: reject repair
- `verification_failed`: rerun needed
- `unchanged`: continue repair

The underlying verification evidence remains the source of truth in `verify/compare.json`; the session summary is a workflow-level index and human-readable outcome.

## GitHub Summary Publishing

`qa-z github-summary` can surface the completed repair outcome in GitHub Actions Job Summary Markdown. The section appears when:

- the source run has `verify/summary.json`, `verify/compare.json`, and `verify/report.md`
- a completed session manifest points at the source run as its candidate
- `--from-session <session>` is provided explicitly

The publish-ready section is intentionally shorter than `outcome.md`. It includes the verdict, resolved blocker count, remaining blocker count, regression count, a PR-friendly recommendation, and short artifact paths for the session, verify summary, verify compare, verify report, outcome, and handoff when available.

Publish recommendations are derived only from recorded verification verdicts:

- `improved`: `safe_to_review`
- `mixed`: `review_required`
- `regressed`: `do_not_merge`
- `verification_failed`: `rerun_required`
- `unchanged`: `continue_repair`

This publishing layer writes or prints Markdown for CI surfaces. It does not create GitHub bot comments, Checks API results, PR status changes, commits, pushes, live executor jobs, or remote orchestration.

## Autonomy Integration

`qa-z autonomy` can prepare a repair session when the selected backlog item is a verification regression and the referenced `verify/compare.json` artifact identifies a baseline run. The autonomy loop records the prepared session in `.qa-z/loops/<loop-id>/outcome.json` and leaves the session in `waiting_for_external_repair`.

Autonomy does not run the external repair, create a candidate rerun, verify the candidate, commit, push, or call Codex or Claude. It only connects selected evidence to the existing local session creation path so a human or external executor has a ready handoff package.

## Executor Bridge

`qa-z executor-bridge` packages a repair session for an external executor:

```bash
python -m qa_z executor-bridge --from-session .qa-z/sessions/<session-id>
python -m qa_z executor-bridge --from-loop .qa-z/loops/<loop-id>
```

The bridge copies the session manifest, handoff JSON, session safety artifacts, optional autonomy outcome, and any existing repair-session action context files into `.qa-z/executor/<bridge-id>/inputs/`, then writes `bridge.json`, `result_template.json`, `executor_guide.md`, `codex.md`, and `claude.md`.

Human stdout includes bridge stdout return pointers for the result template, expected result artifact, copied safety package, safety rule count, and verification command. The bridge guides and stdout also include template placeholder guidance so the scaffolded result summary is replaced before `executor-result ingest`.

When `--output-dir` points outside `.qa-z`, the bridge still writes the requested package but records and prints a `custom_output_dir_outside_qa_z` non-blocking warning so generated executor evidence is not mistaken for policy-managed local QA-Z output. If the path is also outside the repository root, the same warning surfaces include `custom_output_dir_outside_repository` so operators know the copied QA evidence is outside repository cleanup and ignore policy too.

The bridge manifest records the source loop/session, baseline run, handoff paths, selected task ids, validation command, copied input paths, copied action context records under `inputs.action_context`, skipped context paths under `inputs.action_context_missing`, a `safety_package` summary, safety constraints, non-goals, `output_policy`, warnings, and the return contract. The expected return path is still the normal session verification command:

```bash
python -m qa_z repair-session verify --session .qa-z/sessions/<session-id> --rerun
```

The bridge does not invoke Codex, Claude, or any other executor. It does not edit code, run a queue, create a branch, commit, push, post GitHub comments, or apply executor output.

The shared rule set is documented in [pre-live-executor-safety.md](pre-live-executor-safety.md). That document describes the boundary; the session and bridge artifacts are the local machine-readable instances of it.

## Executor Result Ingest

`qa-z executor-result ingest --result <path>` is the strict re-entry path after external repair work. QA-Z now treats the returned result as evidence, not trust:

- freshness is checked against the bridge `created_at` and session `updated_at`
- provenance is checked against the bridge id, session id, and optional loop id
- `completed`, `partial`, `failed`, `no_op`, and `not_applicable` results are classified conservatively
- suspicious results, such as `completed` without `changed_files`, can be accepted with warnings while blocking immediate verify resume
- stale or mismatched results are rejected before they touch the session

Every readable executor result also produces:

```text
.qa-z/executor-results/<result-id>/ingest.json
.qa-z/executor-results/<result-id>/ingest_report.md
```

The ingest artifact records the ingest status, warnings, freshness check, provenance check, verify-resume status, backlog implications, and next recommendation. Accepted results are stored under the session and may resume deterministic verification only when the verify-resume status is `ready_for_verify` or `ingested_with_warning`.

When the owning session can be resolved, every readable executor result attempt also updates:

```text
.qa-z/sessions/<session-id>/executor_results/history.json
.qa-z/sessions/<session-id>/executor_results/attempts/<attempt-id>.json
```

This session-local history is append-only at the contract level: QA-Z records each readable attempt summary with ingest status, verify-resume state, warning ids, backlog categories, and links back to the stored attempt payload plus the ingest artifacts. That lets later dry-run audits and self-inspection reason about repeated partial, rejected, or no-op patterns instead of only the latest accepted result.

## Executor Result Dry-Run

`qa-z executor-result dry-run --session <session>` audits the recorded session attempt history against the same frozen safety package used by repair sessions and bridges:

```bash
python -m qa_z executor-result dry-run --session .qa-z/sessions/<session-id>
python -m qa_z executor-result dry-run --session <session-id> --json
```

It writes:

```text
.qa-z/sessions/<session-id>/executor_results/dry_run_summary.json
.qa-z/sessions/<session-id>/executor_results/dry_run_report.md
```

The summary reports the evaluated attempt count, latest attempt/result status, history-level signals such as repeated partial or verification-blocked patterns, rule-level safety outcomes, an `operator_decision` primary action id, operator summary, ordered recommended actions, and a deterministic next recommendation. The command is live-free: it does not rerun the external executor, mutate the repository, or schedule another retry.

## Future Work

Future work can add standalone annotation helpers or bot/comment integrations after the deterministic local publishing, autonomy, and bridge contracts are stable. Live Codex or Claude execution remains out of scope until deterministic handoff, verification, publishing, autonomy, bridge, executor-result ingest, and pre-live safety contracts are stable.
