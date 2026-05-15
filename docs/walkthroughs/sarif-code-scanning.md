# Walkthrough: SARIF Code Scanning

This walkthrough shows how QA-Z deep evidence becomes GitHub code scanning evidence without adding PR comments, repository mutations, or live execution.

## What QA-Z Writes

Run Semgrep-backed deep checks after a fast run:

```bash
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
```

QA-Z writes SARIF beside the deep summary:

```text
.qa-z/runs/<run-id>/deep/results.sarif
```

For example, the local walkthrough path is:

```text
.qa-z/runs/baseline/deep/results.sarif
```

In the repository CI workflow, the uploaded path is:

```text
.qa-z/runs/ci/deep/results.sarif
```

## Upload To GitHub Code Scanning

SARIF upload is optional because code scanning permissions can vary by repository. To enable upload, the workflow needs:

- `security-events: write`
- `github/codeql-action/upload-sarif@v4`
- a SARIF file path such as `.qa-z/runs/ci/deep/results.sarif`
- a category such as `qa-z-semgrep`

The repository CI workflow uploads QA-Z deep SARIF with:

```yaml
- name: Upload QA-Z SARIF to code scanning
  if: ${{ always() }}
  uses: github/codeql-action/upload-sarif@v4
  continue-on-error: true
  with:
    sarif_file: .qa-z/runs/ci/deep/results.sarif
    category: qa-z-semgrep
```

Composite action users keep upload disabled by default and enable it explicitly with `upload-sarif: "true"` plus `security-events: write`.

## Where To Inspect It

In GitHub, open the repository's code scanning alerts page after the workflow run completes. Identify QA-Z results by the SARIF upload category, for example `qa-z-semgrep`.

The alert surface is repository-owned evidence from the uploaded SARIF. It should be read with the related QA-Z run artifacts, review packet, and repair prompt from the same workflow run.

## Sanitized Capture

See `docs/assets/sarif-code-scanning-capture.md`.

The capture is intentionally text-based so it avoids private repository names, private file contents, user data, tokens, paths that are not needed for the example, and secrets.

## Boundary

QA-Z SARIF upload does not post pull request comments, create branches, commit, push, tag, release, publish packages, deploy, or call live model APIs.
