# Use QA-Z With Semgrep

QA-Z uses Semgrep as a deterministic deep-check engine and keeps the result tied to fast-check evidence.

## Local Deep Gate

```bash
python -m pip install semgrep
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

## SARIF

`qa-z deep` writes:

```text
.qa-z/runs/latest/deep/results.sarif
```

GitHub workflows upload that SARIF with `github/codeql-action/upload-sarif@v4`.

## Policy

Set Semgrep severity, config, ignored rules, and excluded paths in `qa-z.yaml`:

```yaml
deep:
  fail_on_missing_tool: true
  checks:
    - id: sg_scan
      run: ["semgrep", "--config", "auto", "--json"]
      kind: static-analysis
      semgrep:
        config: auto
        fail_on_severity: ["ERROR"]
        ignore_rules: []
```

QA-Z does not reclassify findings with an LLM. It records deterministic findings, filters configured suppressions, and sends blocking evidence to review and repair packets.
