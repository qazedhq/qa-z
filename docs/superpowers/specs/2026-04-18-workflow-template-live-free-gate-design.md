# Workflow Template Live-Free Gate Design

## Context

QA-Z's shipped GitHub workflows are deterministic CI gates. They install QA-Z,
run fast and deep checks, preserve review/repair/summary artifacts, upload SARIF
when available, and fail only after artifacts are written. They are not live
executor workflows and should not imply autonomous repair, branch mutation,
commits, pushes, or GitHub bot comments.

The roadmap still lists report, template, and example sync as an active
hardening lane. The existing workflow tests already protect command order,
SARIF upload, artifact upload, and final fast/deep verdict handling. The next
gap is boundary clarity: the workflows themselves and README should state the
live-free CI gate contract so template drift is visible in review and test
failure output.

## Goal

Pin the workflow-template contract as a live-free deterministic gate without
changing the runtime command sequence.

## Non-Goals

- Do not add live Codex, Claude, or other executor calls.
- Do not create branches, commits, pushes, PR comments, Checks API calls, or
  automatic repair execution.
- Do not change fast/deep/review/repair/github-summary command ordering.
- Do not add network dependencies beyond the already documented GitHub Actions
  and package installation steps.

## Design

### Workflow Boundary Text

Both the repository CI workflow and the reusable template workflow should carry
the same short comment block near the top:

- QA-Z workflow templates are deterministic CI gates.
- This deterministic CI gate preserves local artifacts before applying the
  fast/deep verdict.
- This workflow does not call live executors, mutate branches, commit, push, or
  post bot comments.

This is documentation inside the workflow file, not a new runtime flag. Keeping
it in the file makes copied templates honest even when read outside the README.

### Tests

Extend `tests/test_github_workflow.py` so each protected workflow must include
the boundary phrases in its raw text. This keeps the contract tied to the same
test that already checks command order, SARIF upload, artifact upload, and final
verdict behavior.

The first test run should fail before the workflow comments are added, proving
the guard detects the current sync gap.

### README Sync

Update the workflow paragraph in `README.md` to name the same live-free boundary.
The README should say the included CI workflow remains a deterministic gate: it
preserves artifacts, publishes summaries, uploads SARIF and run artifacts, then
fails from the original fast/deep verdicts. It should also state that it does
not run executor bridges, ingest executor results, perform autonomous repair,
commit, push, or post GitHub bot comments.

## Success Criteria

- The focused workflow test fails before workflow comments are added.
- Both `.github/workflows/ci.yml` and
  `templates/.github/workflows/vibeqa.yml` include the live-free gate boundary.
- README workflow language matches the same boundary.
- Focused workflow tests pass.
- Full pytest passes.
- Benchmark still passes.
