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
.qa-z/runs/baseline/deep/results.sarif
```

GitHub workflows upload that SARIF with `github/codeql-action/upload-sarif@v4`.

## Custom Rule Example

The FastAPI auth-bug example uses a local custom rule file:

```text
examples/fastapi-agent-bug/semgrep-rules/auth-bypass.yml
```

Its `qa-z.yaml` points the `sg_scan` deep check at that file:

```yaml
deep:
  fail_on_missing_tool: true
  checks:
    - id: sg_scan
      run: ["semgrep", "--config", "semgrep-rules/auth-bypass.yml", "--json", "app"]
      kind: static-analysis
      semgrep:
        config: semgrep-rules/auth-bypass.yml
        fail_on_severity: ["ERROR"]
```

From `examples/fastapi-agent-bug`, the vulnerable baseline is expected to
produce 2 findings: `qa-z.fastapi-auth-bypass-any-signed-in-user` and
`qa-z.fastapi-auth-bypass-missing-owner-check`.

This example satisfies the custom-rule workflow: the local `qa-z.yaml` config
points QA-Z deep at `semgrep-rules/auth-bypass.yml`, QA-Z writes SARIF under
`.qa-z/runs/baseline/deep/results.sarif`, and the flow remains local and
deterministic without live services.

```bash
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
```

Raw Semgrep answers "what did this rule match?" QA-Z deep keeps that result
tied to the fast run, applies the configured severity policy, writes
`.qa-z/runs/baseline/deep/summary.json`, writes
`.qa-z/runs/baseline/deep/results.sarif`, and feeds blocking findings into
review and repair packets. Do not commit generated `.qa-z` runtime evidence.

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
        exclude_paths: []
```

`qa-z doctor` validates this policy before a deep run. `semgrep` must be a
mapping, `config` must be a non-empty string, and `fail_on_severity`,
`ignore_rules`, and `exclude_paths` must be lists of non-empty strings.
The policy is applied only to the built-in `sg_scan` deep check. Unknown Semgrep
policy keys fail validation so typos do not silently fall back to default
blocking behavior. Blocking severities are limited to `INFO`, `WARNING`, `WARN`,
and `ERROR`.

`fail_on_severity` controls which normalized findings fail the gate.
`ignore_rules` filters known rule IDs from active blocking findings, and
`exclude_paths` removes configured paths from active findings while preserving
the raw Semgrep run evidence in local artifacts.

QA-Z does not reclassify findings with an LLM. It records deterministic findings, filters configured suppressions, and sends blocking evidence to review and repair packets.

The examples remain local and deterministic. They do not call live services,
live model APIs, package registries, hosted queues, or non-Semgrep deep engines.
