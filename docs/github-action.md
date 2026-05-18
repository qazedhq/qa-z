# GitHub Action

Use the composite guard action when you want QA-Z's demo story to become a real
pull-request gate: `qa-z guard` runs in CI, reviewers read deterministic merge
evidence, and optional outputs stay explicit.

## 1. Minimal PR Gate

Start here. This is the 5-minute copy-paste path for pull requests. It keeps the
workflow token read-only and does not enable SARIF upload or bot comments.

```yaml
name: QA-Z

on:
  pull_request:

jobs:
  qa-z:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      actions: read
    steps:
      - uses: actions/checkout@v6
        with:
          persist-credentials: false
      - uses: qazedhq/qa-z/.github/actions/guard@main
        with:
          profile: python
          deep: auto
          adapter: codex
```

Start with `contents: read` and `actions: read`.

The action installs QA-Z from GitHub during alpha, validates the `profile`
input, runs `qa-z doctor`, then runs
`qa-z guard --deep <input> --adapter <input> --github-summary`.

The `profile` input records the intended starter profile for examples and
validates accepted values. Existing `qa-z.yaml` remains the source of truth for
guard execution.

The composite action validates `qa-z doctor --json`, runs the guard verdict
step, then preserves the summary, optional SARIF, and QA-Z run artifacts with
`always()` cleanup steps.

## 2. PR Summary / Artifacts

The composite action writes QA-Z reviewer output to the GitHub Actions Job Summary.

The summary source is:

```text
.qa-z/runs/latest/guard/github-summary.md
```

If that file is not available, the action falls back to:

```text
.qa-z/runs/latest/guard/verdict.md
```

The uploaded artifact is:

```text
qa-z-runs
```

and it contains the local run evidence under:

```text
.qa-z/runs/latest
```

Reviewers should follow the Job Summary first, then inspect uploaded artifacts
when they need the machine-readable evidence behind the verdict.

The job summary is a deterministic review surface. It is produced from QA-Z run
artifacts and does not rely on live model execution, bot comments, package
publishing, commits, pushes, tags, releases, or deployments.

See `docs/assets/github-actions-summary-capture.md` for a sanitized capture.

PR comments and bot comments are opt-in. Do not enable bot comments by default.
If you later use a comment template, enable it intentionally and review the
extra `pull-requests: write` permission first.

## 3. SARIF Upload Opt-In

SARIF upload is disabled by default because code scanning permissions can be
repository-specific.

Add `security-events: write` only when SARIF upload is enabled. To upload SARIF,
add that permission and set `upload-sarif: "true"`:

```yaml
permissions:
  contents: read
  actions: read
  security-events: write

steps:
  - uses: actions/checkout@v6
    with:
      persist-credentials: false
  - uses: qazedhq/qa-z/.github/actions/guard@main
    with:
      upload-sarif: "true"
```

For a walkthrough of where uploaded SARIF appears in GitHub code scanning, see
`docs/walkthroughs/sarif-code-scanning.md`.

The action does not comment on pull requests, commit, push, or require write
permissions by default.
