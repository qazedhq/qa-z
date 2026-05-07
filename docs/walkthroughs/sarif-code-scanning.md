# Walkthrough: SARIF Code Scanning

Run Semgrep-backed deep checks:

```bash
qa-z fast
qa-z deep --from-run latest
```

QA-Z writes:

```text
.qa-z/runs/latest/deep/results.sarif
```

The GitHub workflow uploads the file with:

```yaml
uses: github/codeql-action/upload-sarif@v4
with:
  sarif_file: .qa-z/runs/pr/deep/results.sarif
```

The result is code-scanning evidence tied to the same QA-Z run as fast checks and repair prompts.
