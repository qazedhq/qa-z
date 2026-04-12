# QA-Z Deep Semgrep Vertical Slice Design

## Goal

Add the first `qa-z deep` vertical slice by running Semgrep as a deterministic, higher-cost verification layer after fast checks. Deep should increase confidence after `qa-z fast` without replacing deterministic pass/fail gates or adding LLM-only judgment.

The initial scope is intentionally narrow:

- Add an executable `qa-z deep` command.
- Normalize Semgrep JSON into QA-Z check results.
- Reuse the existing run summary schema v2 shape.
- Attach deep artifacts to the latest fast run when that is safe.
- Extend review, repair, and GitHub summary to consume deep context from the same run.

## Confirmed Run Attachment Policy

`qa-z deep` defaults to attaching to the latest valid fast run. If attachment is not possible, it creates a new run directory and writes deep artifacts there.

Attachment is allowed only when all of these are true:

- `.qa-z/runs/latest-run.json` exists.
- The manifest points to an existing run directory.
- The run directory contains `fast/summary.json`.

If any condition fails, `qa-z deep` creates a new run under the configured runs root. Deep-only runs still update `latest-run.json`, so later commands can resolve them with `--from-run latest`.

CLI precedence:

1. `--output-dir` wins and is treated as the run directory root.
2. `--from-run` resolves an explicit run root, deep directory, summary path, or `latest`.
3. No explicit input uses the default latest-fast-attach behavior.

The deep summary records the chosen policy as:

```json
{
  "run_attachment_mode": "attached"
}
```

Valid values are `attached` and `new_run`.

## Approaches Considered

### Recommended: Reuse Fast Contracts With Deep-Specific Selection

Deep uses the existing `RunSummary`, `CheckPlan`, `CheckResult`, and `SelectionSummary` models. A dedicated deep runner resolves checks and selection rules, then writes artifacts through the same summary writer with mode `deep`.

Trade-offs:

- Pros: minimal schema churn, current review/repair/GitHub surfaces can be extended incrementally, fewer new abstractions.
- Cons: `CheckResult` needs optional findings metadata for Semgrep.

### Separate Deep Artifact Model

Deep could define a parallel artifact model centered on security findings rather than checks.

Trade-offs:

- Pros: Semgrep findings map directly into a purpose-built structure.
- Cons: review, repair, GitHub summary, and schema docs would need a second consumer path immediately.

### Shell-Only Deep Wrapper

Deep could initially shell out to Semgrep and store raw JSON without normalization.

Trade-offs:

- Pros: fastest to ship.
- Cons: violates QA-Z's bias toward repairable feedback and deterministic contracts; consumers would parse raw Semgrep output themselves.

Recommendation: use the first approach.

## CLI

Supported first-slice commands:

```bash
qa-z deep
qa-z deep --selection full
qa-z deep --selection smart
qa-z deep --from-run latest
qa-z deep --output-dir .qa-z/runs/ci
qa-z deep --json
```

`--selection` defaults to `deep.selection.default_mode`, falling back to `full`.

`--from-run` defaults to the latest-fast-attach policy described above.

`--output-dir` is the run directory root. The summary writer writes deep artifacts under `<run>/deep/`.

## Configuration

`qa-z.yaml` gains a top-level `deep` section:

```yaml
deep:
  output_dir: .qa-z/runs
  fail_on_missing_tool: true
  selection:
    default_mode: full
    full_run_threshold: 15
    high_risk_paths:
      - qa-z.yaml
      - pyproject.toml
      - package.json
      - tsconfig.json
      - eslint.config.js
      - vitest.config.ts
  checks:
    - id: sg_scan
      enabled: true
      run: ["semgrep", "--config", "auto", "--json"]
      kind: static-analysis
```

Legacy `checks.deep` remains contract/planning guidance only. Executable deep checks come from `deep.checks`.

## Components

### `src/qa_z/runners/deep.py`

Orchestrates the deep run:

- Resolve contract context when available.
- Resolve run directory using the attachment policy.
- Resolve deep checks from config.
- Resolve change set from `--diff`, fast summary selection metadata, contract metadata, or none.
- Build deep selection plans.
- Execute Semgrep checks.
- Write `RunSummary` with mode `deep`, schema version 2, and attachment metadata.

Exit code policy matches fast:

- `0`: passed, skipped-only, or warning-only.
- `1`: failed findings.
- `2`: usage/configuration error.
- `3`: missing required tool when configured to fail.
- `4`: no supported deep checks configured.

### `src/qa_z/runners/selection_deep.py`

Builds conservative smart-selection plans for `sg_scan`.

Rules:

- `full`: requested full mode, high-risk change, config change, changed file count over threshold, mixed Python/TypeScript source changes, unknown file kind, deleted/renamed files, or missing/empty change metadata.
- `targeted`: only Python or TypeScript source/test files changed.
- `skipped`: docs-only changes.

Targeted command:

```bash
semgrep --config auto --json <target_paths...>
```

The planner preserves the configured Semgrep base command when possible and appends target paths for targeted scans.

### `src/qa_z/runners/semgrep.py`

Normalizes Semgrep JSON into QA-Z findings:

```json
{
  "rule_id": "python.lang.security.audit.eval",
  "severity": "ERROR",
  "path": "src/app.py",
  "line": 42,
  "message": "Avoid use of eval"
}
```

The parser reads `results[]` and extracts:

- `check_id` as `rule_id`.
- `extra.severity` as `severity`, defaulting to `UNKNOWN`.
- `path`.
- `start.line`.
- `extra.message`.

Semgrep findings count determines the normalized check status:

- findings count > 0: `failed`.
- findings count = 0 and Semgrep exit code is 0: `passed`.
- invalid Semgrep JSON with nonzero exit: keep subprocess failure.
- invalid Semgrep JSON with zero exit: `error`.

### `src/qa_z/reporters/deep_summary.py`

Renders `deep/summary.md` in a compact, repairable format:

- status
- run attachment mode
- selection
- findings count
- severity summary
- affected files
- top findings

The implementation adds a dedicated deep Markdown renderer and lets the shared artifact writer select it when `summary.mode == "deep"`.

## Schema Extension

Deep keeps `summary.json` schema version 2 and adds optional check-level fields:

```json
{
  "id": "sg_scan",
  "kind": "static-analysis",
  "findings_count": 3,
  "severity_summary": {
    "ERROR": 1,
    "WARNING": 2
  },
  "findings": []
}
```

Existing consumers that only read check ids, statuses, totals, and selection metadata remain compatible.

Run-level optional metadata:

```json
{
  "run_attachment_mode": "attached"
}
```

This is stored in an optional summary metadata field rather than as a new required top-level field.

## Data Flow

1. CLI parses `qa-z deep` options.
2. Config loader reads `deep.*`.
3. Deep run resolver picks a run directory:
   - explicit `--output-dir`
   - explicit `--from-run`
   - attach to latest valid fast run
   - create a new run
4. Selection resolves from:
   - explicit `--diff`
   - attached fast summary selection changed files
   - contract change metadata
   - no change metadata
5. Selection planner creates an `sg_scan` `CheckPlan`.
6. Semgrep runs via subprocess unless skipped.
7. Semgrep JSON is normalized into findings metadata.
8. `deep/summary.json`, `deep/summary.md`, and `deep/checks/sg_scan.json` are written.
9. `latest-run.json` points to the containing run directory.

## Error Handling

Missing Semgrep:

- Fails with exit code 3 when `deep.fail_on_missing_tool` is true.
- Skips with a clear message when false.

Malformed Semgrep JSON:

- Becomes an `error` result when the process otherwise succeeded.
- Leaves stdout/stderr tails intact for diagnosis.

No deep checks:

- Produces `unsupported` summary and exit code 4.

Broken latest manifest:

- Does not fail default `qa-z deep`.
- Falls back to a new run and records `run_attachment_mode: new_run`.

Explicit bad `--from-run`:

- Returns usage/source error rather than silently choosing a different run.

## Review, Repair, And GitHub Summary Integration

Existing consumers read sibling `deep/summary.json` when resolving a run. If no deep summary exists, they continue rendering fast-only output.

Review adds:

- security findings summary
- top findings
- affected files

Repair prompt adds:

```md
## Security Findings (Semgrep)

- Avoid use of eval in `src/app.py:42`
```

GitHub summary adds:

```md
## Deep QA

- Findings: 3
- Critical: 1
- Files affected: 2
```

## Tests

Use TDD for implementation. Initial tests:

- `tests/test_deep_selection.py`
  - docs-only changes skip `sg_scan`.
  - Python source-only changes target changed files.
  - TypeScript source-only changes target changed files.
  - mixed Python/TypeScript changes force full.
  - config, deleted, renamed, unknown, and threshold changes force full.
- `tests/test_semgrep_parser.py`
  - extracts rule id, severity, path, line, message.
  - counts severities.
  - produces passed check for empty results.
  - handles malformed JSON deterministically.
- `tests/test_cli.py`
  - `qa-z deep` attaches to latest fast run when valid.
  - `qa-z deep` creates a new deep-only run when no valid fast run exists.
  - `--output-dir` wins over attachment.
  - `--json` prints summary JSON.
- `tests/test_repair_prompt.py`
  - repair prompts include a Security Findings section when deep findings exist.
- `tests/test_github_summary.py`
  - GitHub summaries include a Deep QA section when deep summaries exist.
- `tests/test_artifact_schema.py`
  - optional findings metadata round trips.
  - legacy summaries without findings still load.

## Documentation Updates

When implementation lands:

- Update `README.md` with supported `deep` behavior and missing future surfaces.
- Update `qa-z.yaml.example` with `deep.*`.
- Update artifact schema docs with `deep/summary.json`, `deep/summary.md`, and `deep/checks/*.json`.
- Update `docs/mvp-issues.md` to mark Semgrep deep as the v0.3.0 first vertical slice.

## Out Of Scope

- SARIF upload.
- GitHub PR annotations.
- Multiple deep engines.
- LLM-based security review.
- Automatic Semgrep installation.
- Additional deep engines beyond Semgrep.
