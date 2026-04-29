# QA-Z architecture

QA-Z is a local, model-agnostic QA control plane. Its core job is to turn code-review context into deterministic contracts, checks, artifacts, and repair handoff material.

## Core layers

- CLI and command registration: `src/qa_z/cli.py` and `src/qa_z/commands/` own the public command surface and route command handlers.
- Config and validation: `src/qa_z/config.py`, `src/qa_z/config_validation.py`, and command-level doctor logic load `qa-z.yaml`, check config shape, and keep local onboarding explicit.
- Contracts and planning: `src/qa_z/contracts/`, `src/qa_z/planner/`, and planning commands create QA contracts from titles, issues, specs, and diff excerpts.
- Fast and deep runners: `src/qa_z/runners/` executes deterministic fast checks and Semgrep-backed deep checks, then normalizes tool output into run summaries and SARIF.
- Artifact model: `src/qa_z/artifacts.py` plus verification artifact modules define the local `.qa-z/**` evidence model and shared loading/writing behavior.
- Reporters and GitHub summary: `src/qa_z/reporters/` renders review packets, run summaries, SARIF, and GitHub Actions summary markdown from existing artifacts.
- Repair prompts and adapters: `src/qa_z/repair_handoff.py`, `src/qa_z/adapters/`, and repair command modules render Codex, Claude, and human handoff material without calling live model APIs.
- Repair sessions and verification: `src/qa_z/repair_session*.py` and `src/qa_z/verification*.py` package local repair sessions and compare baseline/candidate run artifacts after a human or external tool makes changes.
- Executor bridge and result ingest: `src/qa_z/executor_bridge*.py`, `src/qa_z/executor_result*.py`, and `src/qa_z/executor_ingest*.py` package external-executor context and ingest returned results for deterministic verification.
- Benchmarks: `src/qa_z/benchmark*.py` owns seeded benchmark fixtures, execution summaries, and benchmark artifact reporting.
- Autonomy planning: `src/qa_z/autonomy*.py`, `src/qa_z/self_improvement*.py`, and backlog modules run deterministic planning loops and surface improvement tasks without editing source code by themselves.

## What is intentionally not here

- No live model execution.
- No autonomous code editing.
- No hidden network calls in local QA flows.
- No automatic commits, pushes, branches, or GitHub comments.

Codex and Claude support remains adapter-oriented. QA-Z writes handoff material for external tools; the core planner and runners stay model-agnostic.
