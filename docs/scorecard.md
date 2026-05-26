# Scorecards

QA-Z exposes two different scorecard surfaces:

- `qa-z scorecard` is a local, read-only QA-Z readiness report for a repository.
- OpenSSF Scorecard is the repository security-practice workflow that uploads SARIF
  from GitHub Actions.

Do not treat either surface as a package release, PyPI publish, deploy, or live
PyPI install claim. Production PyPI is not published.

## QA-Z Scorecard

Run the local scorecard when you want a first-read answer to:

- is this repository configured for QA-Z;
- do the configured profile and repository signals line up;
- are fast checks and deep Semgrep checks ready;
- is there repair-prompt and verify evidence for the latest run;
- is the GitHub Action wired;
- is installed-package smoke evidence present when this is a QA-Z source checkout;
- is the latest evidence bundle fresh enough to navigate.

```powershell
qa-z scorecard
qa-z scorecard --json
qa-z scorecard --markdown
```

The command is read-only unless `--output` is supplied. It does not run the
benchmark, create `.qa-z/**`, install Semgrep, publish packages, post comments,
open pull requests, deploy, tag, or call live coding agents.

### Statuses

Scorecard dimensions use coarse readiness states instead of fake precision:

- `ready`: enough local evidence or configuration exists for that dimension.
- `warning`: the dimension can be inspected, but something limits confidence.
- `blocked`: a required local prerequisite is missing or invalid.
- `not_configured`: the dimension is optional or waits for another workflow step.
- `unknown`: the dimension does not apply or cannot be inferred locally.

The top-level status is derived from the dimensions. A blocked config makes the
whole scorecard `blocked`; missing Semgrep normally produces `warning`; optional
surfaces that do not apply stay `unknown`.

### Dimensions

`qa-z scorecard --json` returns a stable payload with:

- `status`
- `version`
- `dimensions`
- `summary`
- `next_actions`
- `warnings`

Each dimension contains:

- `id`
- `status`
- `message`
- `evidence`
- `suggestion`
- `next_actions`

Current dimension ids are:

- `project_config`
- `profile`
- `fast_checks`
- `deep_semgrep`
- `benchmark_corpus`
- `repair_prompt`
- `verify`
- `github_action`
- `installed_package_smoke`
- `evidence_freshness`

### Common Fixes

- Missing `qa-z.yaml`: run `qa-z init`.
- Profile mismatch: review `project.languages`, run `qa-z doctor --json`, and
  use `qa-z init --help` to see the starter profiles available in this build.
- Missing Semgrep: install Semgrep if you want deep static-analysis coverage.
- No latest evidence: run `qa-z guard --adapter codex --deep auto`.
- Repair prompt missing for a blocked run: run
  `qa-z repair-prompt --from-run latest --adapter codex`.
- Verify missing after repair: run `qa-z verify --from-run latest`.
- GitHub Action missing: run `qa-z init --with-github-workflow` or copy the
  documented workflow from [GitHub Action](github-action.md).
- Benchmark corpus present but no local summary: run `qa-z benchmark --json`.

### Example

```text
QA-Z Scorecard: warning

READY project config: qa-z.yaml loaded and validated.
READY profile: profile signals match configured languages: python.
READY fast checks: 4 enabled fast check(s) configured.
WARN deep/Semgrep: Semgrep not found; deep checks may be limited.
READY benchmark corpus: 52 benchmark fixture(s) available for local readiness proof.
MISS repair prompt: no latest run is available for repair prompt readiness.

Next actions:
1. Install Semgrep
2. Run `qa-z guard --adapter codex --deep auto`
3. Run `qa-z benchmark --json`
```

## OpenSSF Scorecard

QA-Z claims to improve trust in AI-generated code, so the repository should expose its own trust surface.

## Workflow

The repository includes a repository-owned Scorecard workflow:

```text
.github/workflows/scorecard.yml
```

It runs `ossf/scorecard-action@v2.4.0` from GitHub Actions on:

- weekly schedule;
- manual `workflow_dispatch`;
- `branch_protection_rule` updates.

The workflow uploads `scorecard-results.sarif` through `github/codeql-action/upload-sarif@v4` so the result lands in GitHub code scanning.

## Why It Matters

OpenSSF Scorecard gives maintainers and adopters a reproducible view of repository security practices. For QA-Z, it supports the product message: deterministic evidence should apply to the tool itself, not only to user repositories.

## Permission Boundary

The Scorecard workflow is repository trust evidence, not an autonomous QA-Z repair or publishing step.

- `contents: read` lets the workflow inspect repository contents.
- `security-events: write` is limited to uploading Scorecard SARIF.
- `publish_results: false` avoids publishing the result to the public Scorecard API from this workflow.
- The workflow does not post pull request comments, create branches, commit, push, tag, publish packages, deploy, or call live coding agents.

## Inspect The First Run

After the first OpenSSF Scorecard workflow run, inspect:

- the GitHub Actions run for `.github/workflows/scorecard.yml`;
- the uploaded `scorecard-results.sarif` result;
- GitHub code scanning alerts under the `openssf-scorecard` category.

Do not claim a current OpenSSF score from local validation. The score and findings must come from the GitHub Actions run or uploaded SARIF result.

Do not add or advertise a numeric Scorecard badge unless the score source, refresh cadence, and interpretation rules are documented. The current repository-owned evidence surface is the GitHub Actions workflow plus uploaded SARIF.

## Turn Scorecard Findings Into QA-Z Tasks

Each Scorecard finding should become a deterministic follow-up task, not a vague security goal. Convert findings into repository hardening work with a concrete source, scope, validation command, and non-goals.

Use this mapping:

- Branch protection finding -> CI, branch-protection docs, or repository settings task.
- Token permission finding -> workflow permission tightening task.
- Dependency or packaging finding -> release or package checklist task.
- Security policy finding -> `SECURITY.md` or support docs task.
- Binary or artifact finding -> generated-artifact policy task.

A follow-up task should include:

- finding source;
- affected file or repository setting;
- expected deterministic change;
- validation command;
- non-goals;
- generated-artifact policy.

## Follow-up Issue Template

```text
Title:
Fix Scorecard finding: <finding name>

Source:
- Workflow run:
- SARIF/category:
- Finding/check:
- Affected file or setting:

Deterministic change:
- ...

Validation:
- ...

Non-goals:
- No package publish
- No tag/release/deploy
- No bot comment
- No live model execution

Generated-artifact policy:
- Do not commit generated `.qa-z/**`, build, dist, cache, or runtime artifacts.
```

## Local Follow-Up

Scorecard itself runs in GitHub Actions. Local validation is limited to:

```powershell
python -m pytest tests\test_scorecard_docs_current_truth.py -q
python -m pytest tests\test_launch_growth_package.py::test_scorecard_docs_describe_permissions_triggers_and_local_limits tests\test_github_workflow.py -q
python scripts\check_text_file_hygiene.py --source working-tree --critical-profile public
```

Do not claim a current OpenSSF score from local validation. The live score must come from the GitHub Actions run or GitHub code scanning SARIF result.
