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

The action installs QA-Z from GitHub during alpha after validating inputs, runs
`qa-z doctor --json`, then runs `qa-z guard --github-summary`.

## Inputs

- `profile`: documented project profile, default `python`.
- `deep`: guard deep-check policy, default `auto`.
- `adapter`: repair prompt adapter, default `codex`. Supported values are
  `codex`, `claude`, `cursor`, `aider`, `openhands`, `generic`, and legacy
  `human` metadata.
- `fail-on-risk`: exits nonzero on blocking verdicts, default `"true"`.
- `upload-sarif`: uploads `.qa-z/runs/latest/deep/results.sarif`, default `"false"`.
- `from-run`: optional existing run to guard, default empty for a fresh guard run.

Invalid inputs fail before the guard runs and print the invalid input, supported
values, suggested fix, and `docs/github-action.md` troubleshooting link.

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

The Job Summary shows the verdict, top blocked reason, artifact paths, and next
commands. If summary artifacts are missing, the action writes fallback guidance
that points to the expected run, repair prompt, review packet, and SARIF paths.
