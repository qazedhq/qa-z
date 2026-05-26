# GitHub Action

Use the composite guard action when you want QA-Z's demo story to become a real
pull-request gate: `qa-z guard` runs in CI, reviewers read deterministic merge
evidence, and optional outputs stay explicit. If a new workflow fails, start
with the troubleshooting FAQ below before adding permissions or changing the
gate contract.

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

The action installs QA-Z from GitHub during alpha after validating `profile`,
`deep`, `adapter`, `fail-on-risk`, `upload-sarif`, and optional `from-run`
inputs. It then runs `qa-z doctor` and
`qa-z guard --deep <input> --adapter <input> --github-summary`.

The `profile` input records the intended starter profile for examples and
validates accepted values. Existing `qa-z.yaml` remains the source of truth for
guard execution.

Bad action input fails before the guard runs. The error names the invalid input,
the supported values, a suggested fix, and this troubleshooting page.

The composite action validates `qa-z doctor --json`, runs the guard verdict
step, then preserves the summary, optional SARIF, and QA-Z run artifacts with
`always()` cleanup steps.

## 2. PR Summary / Artifacts - Job Summary And Artifact Pointers

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

If `from-run` is set, replace `.qa-z/runs/latest` with that repository-relative
run directory in the summary, SARIF, and artifact upload paths.

Reviewers should follow the Job Summary first. The summary shows the verdict,
top blocked reason, fast/deep statuses, artifact paths, and next commands such
as `qa-z summary --from-run ...`, `qa-z repair-prompt --from-run ...`, and
`qa-z verify --from-run ...`. Inspect uploaded artifacts when you need the
machine-readable evidence behind the verdict.

If QA-Z cannot write the normal summary, the action writes a fallback Job
Summary that lists the missing run directory, expected guard verdict, repair
prompt, review packet, SARIF path, and next diagnostic commands instead of
leaving the summary blank.

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

The older full fast/deep reusable action, `.github/actions/qa-z`, also keeps
SARIF upload disabled by default. Set its `upload-sarif: "true"` input only in a
job that explicitly grants `security-events: write`.

The action does not comment on pull requests, commit, push, or require write
permissions by default.

## 4. Troubleshooting FAQ

### Minimal workflow fails because permissions are too small or wrong

Keep the minimal job at:

```yaml
permissions:
  contents: read
  actions: read
```

Use job-level permissions on the `qa-z` job and keep
`actions/checkout@v6` configured with `persist-credentials: false`. Do not add
`contents: write`, `pull-requests: write`, or broad default write scopes to make
the minimal gate pass. If the failing step is SARIF upload, use the SARIF
answer below instead of changing the minimal workflow.

### SARIF upload fails

SARIF upload is optional. The minimal PR gate should leave `upload-sarif` unset
or `"false"`.

When you intentionally enable SARIF upload, add `security-events: write` to the
same job and set `upload-sarif: "true"`. If GitHub code scanning is disabled,
unavailable for the repository, or restricted by organization policy, the guard
evidence still lives in the Job Summary and `qa-z-runs` artifact.

The summary still points to `.qa-z/runs/latest/deep/results.sarif` even when
upload is skipped or unavailable, so you can inspect the artifact without
granting code scanning permissions.

### PR comments or bot comments are missing

That is expected for the minimal action. QA-Z does not post pull request
comments by default, and the minimal workflow should not request
`pull-requests: write`.

Use the Job Summary and `qa-z-runs` artifact first. If a repository later needs
a comment workflow, enable that path intentionally from a separate template and
review the extra write permission as its own change.

### Where do I find the verdict, repair prompt, Job Summary, and artifacts?

Start in the GitHub Actions Job Summary for the `qa-z` job. The uploaded
artifact is named `qa-z-runs`, and it contains `.qa-z/runs/latest`.

Useful paths inside the artifact:

```text
.qa-z/runs/latest/guard/verdict.md
.qa-z/runs/latest/guard/verdict.json
.qa-z/runs/latest/guard/github-summary.md
.qa-z/runs/latest/review/review.md
.qa-z/runs/latest/repair/<adapter>.md
.qa-z/runs/latest/deep/results.sarif
```

If `repair/<adapter>.md` is absent, inspect `guard/verdict.md` and the fast/deep
summaries first; the guard may not have produced a repair prompt for that run.

If the Job Summary says no run was found, check the install, doctor, fast/deep,
or guard step logs first. For a local repro, run `qa-z doctor --json`, then
`qa-z summary --from-run latest` or `qa-z guard --deep auto --adapter codex`.

### Semgrep or deep checks differ between local and CI

`deep: auto` can skip or downgrade deep evidence when Semgrep is unavailable or
when the repository profile does not select a deep check. CI can also differ
from a local shell if Semgrep is not installed locally, if file paths differ, or
if repository checkout filters hide files.

Compare the Job Summary with the artifact files under
`.qa-z/runs/latest/deep/`, then run the same local profile with `qa-z doctor`
and `qa-z guard --deep auto --adapter <adapter>` before changing CI permissions.

### The profile or adapter does not match my repository

The guard action validates `profile` values of `default`, `python`,
`typescript`, and `monorepo`; `deep` values of `auto`, `always`, and `never`;
`adapter` values of `codex`, `claude`, and `human`; and quoted boolean values
for `fail-on-risk` and `upload-sarif`. For guard execution, an existing `qa-z.yaml` remains the source of truth for actual guard execution. If CI says an input is unsupported,
fix the workflow input. If the wrong checks run, inspect `qa-z.yaml` and run
`qa-z doctor --json` locally.

Use `adapter: codex` or another supported adapter only for repair-prompt
formatting. Changing the adapter should not add write permissions or make QA-Z
edit code. `from-run` should be empty, `latest`, or a repository-relative
`.qa-z/runs/<id>` path; do not point it outside the checkout.

### Why is the PyPI-style pipx install command not shown as live?

QA-Z is still installed from GitHub source in the alpha action and README
examples. TestPyPI/PyPI publishing has not happened yet, so public docs must not
claim that package-registry `pipx` or `uv tool` install commands are live. Keep
GitHub source installs until a separate release-owner publish path is approved
and executed.
