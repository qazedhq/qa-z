# QA-Z Guard Action

Run QA-Z's deterministic merge-safety guard in pull requests.

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
          fail-on-risk: "true"
```

The action installs QA-Z from GitHub during alpha, runs `qa-z doctor --json`,
then runs `qa-z guard --github-summary`. The default `qa-z-install` input pins
the latest GitHub alpha tag and can be overridden for a fork or future release.

## Inputs

- `profile`: documented project profile, default `python`.
- `deep`: guard deep-check policy, default `auto`.
- `adapter`: repair prompt adapter, default `codex`.
- `fail-on-risk`: exits nonzero on blocking verdicts, default `"true"`.
- `upload-sarif`: uploads `.qa-z/runs/latest/deep/results.sarif`, default `"false"`.
- `qa-z-install`: Python package spec used to install QA-Z during alpha,
  default `git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha`.

SARIF upload requires `security-events: write`. Enable it explicitly:

```yaml
permissions:
  contents: read
  actions: read
  security-events: write

steps:
  - uses: actions/checkout@v6
  - uses: qazedhq/qa-z/.github/actions/guard@main
    with:
      upload-sarif: "true"
```

The action does not comment on pull requests, commit, push, create tags, or
require write permissions by default.
