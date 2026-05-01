# GitHub Action

QA-Z ships a pull request gate template and a repository-local composite action.

## Workflow Template

Copy [../templates/.github/workflows/vibeqa.yml](../templates/.github/workflows/vibeqa.yml) into your repository as `.github/workflows/qa-z.yml`.

The workflow:

- installs QA-Z and Semgrep;
- runs `qa-z fast`;
- runs `qa-z deep`;
- renders `qa-z review`, `qa-z repair-prompt`, and `qa-z github-summary`;
- uploads `.qa-z/runs/pr` as an artifact;
- uploads SARIF when `deep/results.sarif` exists;
- fails only after artifacts are preserved.

## Composite Action

The local composite action can be used from this repository:

```yaml
name: QA-Z

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]

jobs:
  qa-z:
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write
    steps:
      - uses: actions/checkout@v4
      - uses: qazedhq/qa-z/.github/actions/qa-z@v0.9.8-alpha
```

The standalone `qazedhq/qa-z-action@v0` repository remains launch roadmap scope. Until that exists, the workflow template is the most stable copy/paste path.

## Non-Goals

The shipped CI path does not call live agents, ingest executor results, perform autonomous repair, create branches, push commits, or post bot comments.
