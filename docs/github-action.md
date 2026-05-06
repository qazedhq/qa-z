# GitHub Action

Use the composite guard action for pull-request evidence.

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
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: qazedhq/qa-z/.github/actions/guard@main
        with:
          profile: python
          deep: auto
          adapter: codex
```

The action installs QA-Z from GitHub during alpha, runs `qa-z doctor`, then runs `qa-z guard --deep <input> --adapter <input> --github-summary`.

The composite action validates `qa-z doctor --json`, then preserves review, repair, summary, optional SARIF, and run artifacts before the final fast/deep verdict step.

SARIF upload is disabled by default because code scanning permissions can be repository-specific.

To upload SARIF, add `security-events: write` and set `upload-sarif: "true"`:

```yaml
permissions:
  contents: read
  actions: read
  security-events: write

steps:
  - uses: actions/checkout@v4
  - uses: qazedhq/qa-z/.github/actions/guard@main
    with:
      upload-sarif: "true"
```

The action does not comment on pull requests, commit, push, or require write permissions by default.
