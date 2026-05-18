# OpenSSF Scorecard

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
