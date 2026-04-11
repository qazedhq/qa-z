# QA-Z

QA-Z is a Python-first QA control plane for coding agents.

It generates QA contracts, runs deterministic fast checks, and emits review/repair packets from run artifacts.

Today, QA-Z can:

- initialize a repository scaffold
- generate QA contracts from issue, spec, and diff inputs
- run deterministic fast checks for Python projects
- emit run-aware review packets
- generate repair prompts from failed run artifacts

QA-Z does not yet implement:

- deep QA runners
- TypeScript fast runners
- SARIF or GitHub annotation output
- live Codex or Claude adapters

## Why this exists

Most agentic coding tools are optimized to generate or edit code. QA-Z is optimized to answer a different question:

> Should this change be merged, and if not, what should the agent fix next?

The project is intentionally:

- `QA-first`, not codegen-first
- `contract-first`, not prompt-only
- `deterministic-gated`, not LLM-judged
- `model-agnostic`, not tied to a single coding agent
- `repair-oriented`, not just pass/fail

## Alpha Status

This repository is targeting `v0.1.0-alpha`: a public Python-first vertical slice, not a finished QA control plane.

The reproducible alpha loop is:

```text
init -> plan -> fast -> review --from-run -> repair-prompt
```

The current implementation includes:

- a public-facing product narrative
- a repository-level `AGENTS.md`
- a starter `qa-z.yaml.example`
- a minimal Python CLI with stable command names
- a working `qa-z plan` contract generator
- a working Python-first `qa-z fast` deterministic runner with JSON and Markdown artifacts
- a working `qa-z review` review-packet generator, including run-aware packets
- a working `qa-z repair-prompt` generator for failed fast runs
- Codex and Claude integration templates
- GitHub workflow examples for CI and Codex review

Roadmap work that is intentionally not part of the alpha:

- dynamic check selection
- TypeScript fast-check orchestration
- property, mutation, or security execution engines
- SARIF or GitHub annotation reporters
- live Codex or Claude adapter runtimes

## Command surface

QA-Z reserves these commands from day one:

```text
qa-z init
qa-z plan
qa-z fast
qa-z deep
qa-z review
qa-z repair-prompt
```

In this bootstrap, `init`, `plan`, `fast`, `review`, and `repair-prompt` are functional. `deep` still returns structured guidance for the capability it will own.

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

Run the Python fast gate and write JSON/Markdown artifacts:

```bash
python -m qa_z fast
python -m qa_z fast --json
python -m qa_z fast --output-dir .qa-z/runs/local
python -m qa_z fast --strict-no-tests
```

Render a review packet from a run:

```bash
python -m qa_z review --from-run latest
python -m qa_z review --from-run .qa-z/runs/local --json
```

Generate an agent-friendly repair packet from the latest fast run:

```bash
python -m qa_z repair-prompt
python -m qa_z repair-prompt --from-run latest
python -m qa_z repair-prompt --from-run .qa-z/runs/local
python -m qa_z repair-prompt --json
```

Run the local verification suite:

```bash
python -m pytest
```

## Example policy

`qa-z.yaml.example` shows the intended policy shape:

```yaml
project:
  name: qa-z
  languages:
    - python
fast:
  output_dir: .qa-z/runs
  strict_no_tests: false
  fail_on_missing_tool: true
  checks:
    - id: py_lint
      enabled: true
      run: ["ruff", "check", "."]
      kind: lint
    - id: py_format
      enabled: true
      run: ["ruff", "format", "--check", "."]
      kind: format
    - id: py_type
      enabled: true
      run: ["mypy", "src", "tests"]
      kind: typecheck
    - id: py_test
      enabled: true
      run: ["pytest", "-q"]
      kind: test
      no_tests: warn
```

The long-term design is for QA-Z to combine:

- repository metadata
- issue or PR context
- explicit QA contracts
- deterministic runner outputs
- agent-friendly repair packets

Today, `qa-z plan` turns a title plus optional source files into a contract draft under `qa/contracts/`, `qa-z fast` runs configured deterministic Python checks and writes run artifacts under `.qa-z/runs/`, `qa-z review` turns contracts or fast runs into reusable review packets, and `qa-z repair-prompt` writes `packet.json` plus `prompt.md` under the source run's `repair/` directory.

See `docs/artifact-schema-v1.md` for the required `summary.json` and repair packet fields.

## Repository map

```text
docs/                     design notes, plans, artifact schema, and MVP backlog
qa/contracts/             QA contract workspace
src/qa_z/                 Python package and CLI surface
templates/                downstream Codex and Claude integration templates
.github/workflows/        CI and Codex review workflows for this repo
examples/                 runnable and planned demos
benchmark/                planned seeded bug and evaluation corpus
```

## Near-term roadmap

1. Add diff-aware check selection for fast runs.
2. Add TypeScript fast checks after the Python runner stays stable.
3. Connect review output directly to PR comments and SARIF reporters.
4. Add live Codex and Claude adapter handoff helpers around repair packets.
5. Add deep checks for property, mutation, security, and smoke E2E.

## Positioning

QA-Z is not another coding agent.

It is the QA layer that helps coding agents reach production quality with traceable contracts, executable checks, and actionable repair feedback.
