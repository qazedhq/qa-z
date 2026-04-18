# QA-Z

QA-Z is a Codex-first, model-agnostic QA control plane for coding agents.

It turns local QA contracts, deterministic runner output, deep findings, review packets, repair handoffs, and post-repair verification into explicit evidence that a coding agent or human can act on.

Today, QA-Z can:

- initialize a repository scaffold
- generate QA contracts from issue, spec, and diff inputs
- run deterministic fast checks from configured Python and TypeScript commands
- choose full or smart fast/deep check scope from changed files or an explicit diff
- run Semgrep-backed deep checks and normalize findings, grouped findings, severity counts, and policy decisions
- emit run-aware review packets that include fast check results, selection context, and sibling deep findings
- generate repair prompts plus normalized handoff artifacts and Codex/Claude Markdown renderers from local evidence
- compare baseline and candidate runs with `qa-z verify`
- write SARIF 2.1.0 from normalized deep findings
- run a seeded local benchmark corpus for fast, deep, handoff, and verification behavior

QA-Z does not yet implement:

- live model execution
- remote orchestration, scheduling, or automatic code repair
- GitHub API posting or Checks API annotations
- deep engines beyond the current Semgrep check
- a production plugin system

## Why This Exists

Most agentic coding tools are optimized to generate or edit code. QA-Z is optimized to answer a different question:

> Should this change be merged, and if not, what should be fixed next?

The project is intentionally:

- `QA-first`, not codegen-first
- `contract-first`, not prompt-only
- `deterministic-gated`, not LLM-judged
- `model-agnostic`, not tied to a single coding agent
- `repair-oriented`, not just pass/fail

## Alpha Status

This repository is in an alpha foundation stage. The current reproducible loop is:

```text
init -> plan -> fast -> deep -> review --from-run -> repair-prompt -> verify
```

The current implementation includes:

- a public-facing product narrative
- a repository-level `AGENTS.md`
- a starter `qa-z.yaml.example`
- a Python CLI with stable command names
- a working `qa-z plan` contract generator
- a working `qa-z fast` deterministic runner with JSON and Markdown artifacts
- full and smart fast check selection
- a working `qa-z deep` Semgrep runner with full and smart selection
- normalized deep finding metadata and SARIF output
- a working `qa-z review` review-packet generator with run and deep context
- a working `qa-z repair-prompt` generator for failed fast checks and blocking deep findings
- normalized `handoff.json`, `codex.md`, and `claude.md` repair artifacts
- a working `qa-z verify` comparison command for baseline and candidate run evidence
- a working `qa-z benchmark` runner with seeded Python fast, TypeScript fast, Semgrep deep policy, repair handoff, and verification fixtures
- Codex and Claude integration templates
- workflow examples for local deterministic QA gates

Roadmap work that is intentionally not part of this foundation slice:

- additional deep engines such as CodeQL, Trivy, property checks, mutation checks, and smoke E2E
- live Codex or Claude runtime calls
- remote comments, labels, or hosted status mutations
- autonomous planning or external execution loops

## Command Surface

QA-Z reserves these commands from day one:

```text
qa-z init
qa-z plan
qa-z fast
qa-z deep
qa-z review
qa-z repair-prompt
```

The foundation implementation also includes:

```text
qa-z verify
qa-z benchmark
```

All implemented commands operate on local files and deterministic subprocess output. They do not call live model APIs.

## Quickstart

Install the project locally:

```bash
python -m pip install -e .[dev]
```

Inspect the command surface:

```bash
python -m qa_z --help
```

Initialize a repository with a starter policy:

```bash
python -m qa_z init
```

Generate a first QA contract draft:

```bash
python -m qa_z plan --title "Protect billing auth guard" --issue issue.md --spec spec.md
```

Run fast deterministic checks and write JSON/Markdown artifacts:

```bash
python -m qa_z fast
python -m qa_z fast --json
python -m qa_z fast --selection smart --diff changes.diff
python -m qa_z fast --output-dir .qa-z/runs/local
python -m qa_z fast --strict-no-tests
```

Run Semgrep-backed deep checks attached to the latest fast run, or to an explicit run directory:

```bash
python -m qa_z deep
python -m qa_z deep --json
python -m qa_z deep --from-run .qa-z/runs/local
python -m qa_z deep --output-dir .qa-z/runs/local
python -m qa_z deep --selection smart --diff changes.diff
python -m qa_z deep --sarif-output qa-z.sarif
```

`deep` expects Semgrep on `PATH` when `sg_scan` is enabled. Missing tools and malformed Semgrep output are recorded in run artifacts instead of being hidden.

Render a review packet from a run:

```bash
python -m qa_z review --from-run latest
python -m qa_z review --from-run .qa-z/runs/local --json
```

Generate an agent-friendly repair packet and handoff artifacts from a run:

```bash
python -m qa_z repair-prompt
python -m qa_z repair-prompt --from-run latest
python -m qa_z repair-prompt --from-run .qa-z/runs/local
python -m qa_z repair-prompt --from-run latest --adapter codex
python -m qa_z repair-prompt --from-run latest --adapter claude
python -m qa_z repair-prompt --json
python -m qa_z repair-prompt --handoff-json
```

`repair-prompt` writes `packet.json`, `prompt.md`, `handoff.json`, `codex.md`, and `claude.md` under the source run's `repair/` directory by default.

Verify a candidate run against the original baseline:

```bash
python -m qa_z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
python -m qa_z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate --json
python -m qa_z verify --baseline-run .qa-z/runs/baseline --rerun --rerun-output-dir .qa-z/runs/candidate
```

`verify` compares fast check changes and blocking deep findings, writes `summary.json`, `compare.json`, and `report.md`, and returns a deterministic verdict.

Run the local benchmark corpus:

```bash
python -m qa_z benchmark
python -m qa_z benchmark --json
python -m qa_z benchmark --fixture ts_type_error
```

`benchmark` copies seeded fixtures into `benchmarks/results/work/`, runs deterministic QA-Z flows, compares observed artifacts with `expected.json`, and writes `benchmarks/results/summary.json` plus `benchmarks/results/report.md`.

Run the local verification suite:

```bash
python -m pytest
```

## Example Policy

`qa-z.yaml.example` shows the current policy shape. The important foundation sections are:

```yaml
fast:
  output_dir: ".qa-z/runs"
  selection:
    default_mode: "full"
    full_run_threshold: 40
  checks:
    - id: py_lint
      run: ["ruff", "check", "."]
      kind: "lint"
    - id: ts_type
      run: ["tsc", "--noEmit"]
      kind: "typecheck"

deep:
  fail_on_missing_tool: true
  selection:
    default_mode: "full"
    full_run_threshold: 15
    exclude_paths:
      - dist/**
      - build/**
      - coverage/**
  checks:
    - id: sg_scan
      run: ["semgrep", "--json"]
      kind: "static-analysis"
      semgrep:
        config: "auto"
        fail_on_severity:
          - ERROR
```

The long-term design is for QA-Z to combine:

- repository metadata
- issue or PR context
- explicit QA contracts
- deterministic fast and deep runner outputs
- repair handoffs that preserve exact evidence and validation commands
- verification comparisons after a repair attempt

See `docs/artifact-schema-v1.md` for the required `summary.json`, repair packet, handoff, SARIF, and verification artifact fields.

## Repository Map

```text
docs/                     design notes, plans, artifact schema, benchmarking guide, and MVP issue list
benchmarks/               seeded benchmark fixtures, support helpers, and generated local results
qa/contracts/             QA contract workspace
src/qa_z/                 Python package and CLI surface
templates/                downstream Codex and Claude integration templates
.github/workflows/        local CI workflow examples
examples/                 runnable and planned demos
```

## Near-Term Roadmap

1. Keep fast/deep runner selection stable across Python and TypeScript command configs.
2. Add more deep engines after Semgrep artifacts stay stable.
3. Expand downstream workflow templates around SARIF and local artifacts.
4. Continue hardening repair handoff and verification evidence.
5. Expand benchmark fixtures as new deterministic failure and repair-evidence gaps are found.

## Positioning

QA-Z is not another coding agent.

It is the QA layer that helps coding agents reach production quality with traceable contracts, executable checks, and actionable repair feedback.
