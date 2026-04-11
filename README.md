# QA-Z

QA-Z is a QA control plane for coding agents.

It sits above tools like Codex, Claude Code, Aider, or OpenHands and turns prompts, specs, issues, and diffs into executable QA contracts, merge gates, and repair feedback.

## Why this exists

Most agentic coding tools are optimized to generate or edit code. QA-Z is optimized to answer a different question:

> Should this change be merged, and if not, what should the agent fix next?

The project is intentionally:

- `QA-first`, not codegen-first
- `contract-first`, not prompt-only
- `deterministic-gated`, not LLM-judged
- `model-agnostic`, not tied to a single coding agent
- `repair-oriented`, not just pass/fail

## Bootstrap status

This repository is the first public scaffold. It already includes:

- a public-facing product narrative
- a repository-level `AGENTS.md`
- a starter `qa-z.yaml.example`
- a minimal Python CLI with stable command names
- a working `qa-z plan` contract generator
- a working Python-first `qa-z fast` deterministic runner
- a working `qa-z review` review-packet generator, including run-aware packets
- a working `qa-z repair-prompt` generator for failed fast runs
- Codex and Claude integration templates
- GitHub workflow examples for CI and Codex review

What it does not include yet:

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

Render a review packet from the newest contract:

```bash
python -m qa_z review
python -m qa_z review --from-run latest
python -m qa_z review --from-run .qa-z/runs/local --json
```

Run the Python fast gate and write JSON/Markdown artifacts:

```bash
python -m qa_z fast
python -m qa_z fast --json
python -m qa_z fast --output-dir .qa-z/runs/local
python -m qa_z fast --strict-no-tests
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

## Repository map

```text
docs/                     design notes, plans, and MVP backlog
qa/contracts/             QA contract workspace
src/qa_z/                 Python package and CLI surface
templates/                downstream Codex and Claude integration templates
.github/workflows/        CI and Codex review workflows for this repo
examples/                 planned FastAPI and Next.js demos
benchmark/                planned seeded bug and evaluation corpus
```

## Near-term roadmap

1. Expand contract drafting beyond file-based source inputs into repo and diff ingestion.
2. Add TypeScript fast checks after the Python runner stays stable.
3. Add deep checks for property, mutation, security, and smoke E2E.
4. Connect review output directly to PR comments and SARIF reporters.
5. Add agent adapter handoff helpers around repair packets.

## Positioning

QA-Z is not another coding agent.

It is the QA layer that helps coding agents reach production quality with traceable contracts, executable checks, and actionable repair feedback.
