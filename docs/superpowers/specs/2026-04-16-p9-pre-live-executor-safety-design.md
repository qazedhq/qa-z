# P9 Pre-Live Executor Safety Package Design

## Goal

Freeze QA-Z's pre-live executor safety boundary as one explicit local package that repair sessions, executor bridges, and public docs can all reference consistently before any live executor integration is considered.

## Why Now

QA-Z already has:

- repair-session packaging
- executor bridges
- structured executor-result ingest
- freshness, scope, and verification gating

That means the next risk is not missing workflow plumbing. The risk is that live-executor work could start later with safety policy still scattered across guides, manifests, and docs.

## Design Options

### Option 1: Documentation-only freeze

Update README and docs to list the safety rules in one place.

Pros:

- smallest code change
- easy to review

Cons:

- no machine-readable artifact
- bridge/session flows would still embed policy ad hoc
- future live work would have nothing concrete to point at

### Option 2: Add safety sections only to existing manifests

Extend repair-session and bridge manifests with the same structured safety fields.

Pros:

- machine-readable
- stays close to current artifacts

Cons:

- still duplicates the same policy in multiple places
- weaker as a reusable package boundary

### Option 3: Create one explicit safety package artifact and reference it everywhere

Generate a shared pre-live safety contract under each repair session, then have executor bridges copy and reference that same contract.

Pros:

- one explicit contract package exists
- repair-session and bridge surfaces point to the same rules
- future live work can reuse the package instead of inventing new policy text

Cons:

- slightly larger artifact surface than a docs-only pass

## Recommendation

Choose Option 3.

This is the smallest implementation that actually satisfies the roadmap goal of freezing a pre-live safety package instead of merely restating scattered guidance.

## Scope

P9 adds:

- one structured `qa_z.executor_safety` artifact
- one human-readable safety Markdown companion
- repair-session generation of those artifacts
- repair-session manifest pointers to the safety package
- executor-bridge copying and referencing of the same safety package
- doc and schema updates that point to the package instead of duplicating policy loosely

P9 does not add:

- live Codex or Claude API execution
- automatic retries or redispatch
- remote queues, schedulers, or daemons
- automatic code edits
- branch, commit, push, or GitHub bot behavior

## Safety Rules To Freeze

The package should make these rules explicit:

1. No-op safeguard:
   no-op or not-applicable outcomes require explicit explanation and must not be treated as silent success.
2. Retry boundary:
   QA-Z does not auto-retry, auto-redispatch, or silently rerun an external executor after rejected or partial outcomes.
3. Mutation scope limits:
   external edits must stay within the selected repair-session and bridge scope.
4. Unrelated-refactor prohibition:
   external executors must not broaden scope or bundle opportunistic cleanup outside the declared repair objective.
5. Verification-required completion:
   a `completed` result is not merge-ready until deterministic QA-Z verification has passed or been explicitly attached through approved evidence.
6. Outcome classification policy:
   executor results must be classified honestly as `completed`, `partial`, `failed`, `no_op`, or `not_applicable`, with partial completion preserved rather than disguised.

## Artifact Shape

The JSON artifact should be stable and machine-readable, for example:

```json
{
  "kind": "qa_z.executor_safety",
  "schema_version": 1,
  "package_id": "pre_live_executor_safety_v1",
  "status": "pre_live_only",
  "summary": "Freeze local safety policy before any live executor integration.",
  "rules": [
    {
      "id": "no_op_requires_explanation",
      "category": "no_op_safeguard",
      "requirement": "No-op and not-applicable outcomes require explicit explanation.",
      "enforced_by": ["executor-result ingest warnings"]
    }
  ]
}
```

The Markdown companion should explain the same rules in operator-facing language.

## Artifact Placement

Repair-session start should write:

```text
.qa-z/sessions/<session-id>/executor_safety.json
.qa-z/sessions/<session-id>/executor_safety.md
```

Executor bridge should copy those artifacts into:

```text
.qa-z/executor/<bridge-id>/inputs/executor_safety.json
.qa-z/executor/<bridge-id>/inputs/executor_safety.md
```

## Manifest Integration

Repair-session manifest should gain a `safety_artifacts` mapping that points at the session-local safety files.

Executor bridge manifest should gain:

- copied safety input paths under `inputs`
- a top-level `safety_package` summary with package id, status, path pointers, and rule ids

## Verification And Enforcement Relationship

The new package is not a second validation engine. It is a frozen statement of the rules already enforced or intentionally deferred by QA-Z. Enforcement remains where it already belongs:

- repair-session and bridge packaging for operator guidance
- executor-result ingest for scope, freshness, no-op, and outcome classification checks
- verification for deterministic completion

## Tests

P9 should add deterministic coverage for:

- repair-session safety artifact creation
- repair-session manifest schema stability with `safety_artifacts`
- executor-bridge copying and manifest reference of the safety package
- bridge and session guides mentioning the same safety package instead of ad hoc text only

## Success Criteria

P9 is complete when:

- one explicit safety contract artifact exists
- repair-session and bridge artifacts both reference that package
- public docs reflect the package exactly
- tests and full validation pass
