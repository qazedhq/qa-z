# Generated Versus Frozen Evidence Policy Design

## Goal

Make QA-Z's generated-versus-frozen evidence boundary explicit enough that operators, docs, and self-inspection all agree on what is local runtime output and what may be intentionally committed.

## Problem

QA-Z already ignores root `.qa-z/` state and generated benchmark outputs, and self-inspection can suppress stale artifact-hygiene candidates when those ignore rules exist. That is useful, but too implicit: the code currently treats `.gitignore` coverage as the whole policy. The alpha baseline needs a readable policy document plus deterministic self-inspection evidence so future agents do not infer frozen benchmark evidence rules from scattered reports.

## Chosen Approach

Use a small contract-backed policy layer:

- add `docs/generated-vs-frozen-evidence-policy.md` as the human-readable source of truth
- keep `.gitignore` as the enforcement surface for local runtime artifacts
- make `qa_z.self_improvement.generated_artifact_policy_snapshot()` require both ignore coverage and policy-document coverage before reporting the policy as explicit
- include missing policy rules or missing policy-document terms as candidate evidence when self-inspection detects ambiguity
- add current-truth tests so README/schema/benchmark docs keep pointing at the same policy

## Alternatives Considered

### Docs Only

This would explain the policy but would not stop `self-inspect` from using stale report language as if the policy were still absent.

### Code Only

This would quiet backlog noise, but operators would still need to reverse-engineer the rule from `.gitignore` and Python constants.

### Policy Doc Plus Code Snapshot

This is the selected option. It keeps the implementation small while making the policy reviewable and machine-checkable.

## Policy Contract

The documented policy classifies repository evidence into four groups:

- root `.qa-z/**`: generated runtime state, local only
- `benchmarks/results/work/**`: generated benchmark scratch workspaces, local only
- `benchmarks/results/summary.json` and `benchmarks/results/report.md`: generated benchmark outputs, local by default, commit only as intentional frozen evidence with surrounding docs
- `benchmarks/fixtures/**/repo/.qa-z/**`: fixture-local test vectors, allowed because they are part of deterministic benchmark inputs

## Self-Inspection Behavior

`collect_live_repository_signals()` will expose:

- `generated_artifact_ignore_policy_explicit`
- `generated_artifact_documented_policy_explicit`
- `generated_artifact_policy_explicit`
- `missing_generated_artifact_policy_rules`
- `missing_generated_artifact_policy_terms`
- `generated_artifact_policy_doc_path`

`generated_artifact_policy_explicit` is true only when both ignore rules and the policy document are present. If either side is missing, self-inspection may create an `evidence_freshness_gap` candidate with concrete missing-policy evidence.

When both sides are present and no live runtime artifact paths are dirty, stale report wording alone should not keep artifact-hygiene, runtime-artifact-cleanup, or evidence-freshness tasks open.

## Documentation Surfaces

Update these surfaces:

- `docs/generated-vs-frozen-evidence-policy.md`
- `docs/artifact-schema-v1.md`
- `docs/benchmarking.md`
- `README.md`
- `docs/reports/next-improvement-roadmap.md`
- `docs/reports/current-state-analysis.md`

## Tests

Add tests for:

- policy snapshot requires both ignore rules and the policy document
- self-inspection promotes a policy gap when ignore rules exist but the policy document is missing
- self-inspection suppresses stale policy gaps when ignore rules and the policy document are both present
- current-truth docs mention the policy document and local/frozen benchmark-result rule

## Non-Goals

- no live executor work
- no remote orchestration
- no new command surface
- no deletion of existing local artifacts
- no change to benchmark result formats

## Expected Result

The active roadmap can treat generated-versus-frozen evidence policy as landed once tests pass and self-inspection no longer depends on scattered cleanup notes to decide whether the policy exists.
