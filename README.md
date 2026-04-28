# QA-Z

> Deterministic QA gates for AI coding agents.

[![CI](https://github.com/qazedhq/qa-z/actions/workflows/ci.yml/badge.svg)](https://github.com/qazedhq/qa-z/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-alpha-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)
[![Release](https://img.shields.io/github/v/release/qazedhq/qa-z?include_prereleases&label=release)](https://github.com/qazedhq/qa-z/releases/tag/v0.9.8-alpha)

AI coding agents can write code fast. QA-Z helps you decide whether that code is safe to merge.

QA-Z turns code changes into QA contracts, deterministic checks, review packets, repair prompts, verification evidence, GitHub summaries, SARIF, and benchmark artifacts.

> Should this change be merged — and if not, what should the agent fix next?

## Why QA-Z?

Most coding agents stop at "I changed the code."

QA-Z adds the missing QA layer:

- What changed?
- What should be tested?
- Did fast checks pass?
- Did deep checks find risks?
- What should the agent fix next?
- Did the repair actually improve the result?

## What QA-Z Does

- Generates QA contracts from issues, specs, and diffs
- Runs deterministic fast checks for Python and TypeScript
- Runs Semgrep-backed deep checks and emits SARIF
- Produces review packets and repair prompts
- Packages local repair sessions for Codex, Claude, or humans
- Verifies whether a repair improved, stayed unchanged, mixed fixes with regressions, or regressed
- Publishes GitHub Actions summaries and local artifacts

## Quickstart

Install QA-Z locally:

```bash
python -m pip install -e .[dev]
```

Install Semgrep before running local deep checks:

```bash
python -m pip install semgrep
```

Check the CLI:

```bash
python -m qa_z --help
```

Initialize a repository:

```bash
python -m qa_z init --profile python --with-agent-templates --with-github-workflow
```

Run the short QA loop:

```bash
python -m qa_z doctor
python -m qa_z plan --title "Review recent agent change" --slug agent-change --overwrite
python -m qa_z fast
python -m qa_z deep --from-run latest
python -m qa_z review --from-run latest
python -m qa_z repair-prompt --from-run latest --adapter codex
```

The output is local and artifact-first. Look under `.qa-z/runs/` for the run evidence.

## Core Workflow

```text
init -> plan -> fast -> deep -> review -> repair-prompt -> external repair -> verify -> github-summary
```

QA-Z does not edit your code by itself. It creates the contracts, evidence, prompts, and verification artifacts that make external repair work safer to review.

## Command Surface

| Command | What it does |
| --- | --- |
| `qa-z init` | Create starter QA-Z config and optional templates |
| `qa-z doctor` | Validate config shape and launch readiness |
| `qa-z plan` | Generate a QA contract from issue/spec/diff input |
| `qa-z fast` | Run deterministic fast checks |
| `qa-z deep` | Run configured Semgrep deep checks |
| `qa-z review` | Render a review packet from run artifacts |
| `qa-z repair-prompt` | Generate Codex / Claude / handoff repair prompts |
| `qa-z repair-session` | Package a local repair workflow |
| `qa-z verify` | Compare baseline and candidate run artifacts |
| `qa-z github-summary` | Render GitHub Actions summary Markdown |
| `qa-z benchmark` | Run seeded QA-Z benchmark fixtures |
| `qa-z self-inspect` | Inspect QA-Z artifacts and surface improvement tasks |
| `qa-z select-next` | Select the next self-improvement backlog tasks |
| `qa-z backlog` | Print the current QA-Z improvement backlog |
| `qa-z autonomy` | Run deterministic self-improvement planning loops |
| `qa-z executor-bridge` | Package a repair session for an external executor |
| `qa-z executor-result` | Ingest an external executor result for verification |

## Artifacts

| Path | Purpose |
| --- | --- |
| `.qa-z/runs/` | Fast and deep run evidence |
| `.qa-z/runs/latest/review/` | Review packet output |
| `.qa-z/runs/latest/repair/` | Repair prompt and handoff output |
| `.qa-z/runs/latest/deep/results.sarif` | Deep-check SARIF output |
| `.qa-z/sessions/` | Local repair session packages |
| `.qa-z/executor/` | External executor bridge packages |
| `.qa-z/executor-results/` | Returned executor result ingest artifacts |
| `.qa-z/improvement/` | Self-inspection and backlog artifacts |
| `.qa-z/loops/` | Autonomy planning loop artifacts |

Root `.qa-z/**` is local by default and should normally stay out of release commits.

For detailed operator-contract and current-truth maintenance anchors, see [docs/current-truth-maintenance-anchors.md](docs/current-truth-maintenance-anchors.md).

## Demo Flow

The shortest demo is text-first and uses real CLI commands:

```bash
python -m qa_z plan --title "Review recent agent change" --slug agent-change --overwrite
python -m qa_z fast
python -m qa_z deep --from-run latest
python -m qa_z review --from-run latest
python -m qa_z repair-prompt --from-run latest --adapter codex
python -m qa_z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

`verify` expects existing baseline and candidate run directories; use it after an external repair tool or human fix creates a candidate run. For a fuller transcript, see [docs/demo-script.md](docs/demo-script.md). A runnable TypeScript fast-gate example lives under [examples/typescript-demo/](examples/typescript-demo/).

## What QA-Z Is Not

QA-Z is not:

- a coding agent
- an autonomous code editor
- a live Codex or Claude runtime
- a queue, scheduler, or remote orchestrator
- an LLM-only judge replacing deterministic checks
- a tool that commits, pushes, or posts GitHub comments by itself

QA-Z is the QA layer around those workflows.

## Status

QA-Z is alpha software. The current package metadata targets `0.9.8a0`, published in docs as `v0.9.8-alpha`.

Deep QA automation currently centers on Semgrep-backed checks and deterministic local artifacts. Codex and Claude support is adapter-oriented: QA-Z writes handoff material for external tools instead of calling live model APIs.

## Roadmap

Next up: broader TypeScript deep QA, multi-engine checks, richer GitHub annotations, and stronger mixed Python/TypeScript benchmark realism.

## Docs

- [Artifact schema v1](docs/artifact-schema-v1.md)
- [Repair sessions](docs/repair-sessions.md)
- [Pre-live executor safety](docs/pre-live-executor-safety.md)
- [Generated vs frozen evidence policy](docs/generated-vs-frozen-evidence-policy.md)
- [Current-truth maintenance anchors](docs/current-truth-maintenance-anchors.md)
- [Demo script](docs/demo-script.md)
- [Docs index](docs/README.md)
- [Example config](qa-z.yaml.example)
- [TypeScript demo](examples/typescript-demo/)

## License

Apache-2.0
