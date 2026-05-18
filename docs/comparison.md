# QA-Z Comparison

QA-Z is not a coding agent. QA-Z is a model-agnostic merge evidence layer
around coding agents.

QA-Z does not replace coding agents. Use agents and editors to make the
change. Use QA-Z before merge to turn that change into contracts,
deterministic fast/deep checks, local artifacts, review packets, repair
prompts, and baseline/candidate verification evidence.

## Where QA-Z Fits

This comparison is role-based. It does not rank model quality, benchmark
results, or current feature depth for any coding agent.

| Tool or workflow | Primary role | What it produces | Where QA-Z fits | QA-Z boundary |
| --- | --- | --- | --- | --- |
| Codex | Human-operated coding agent workflow | Code changes and repair attempts | Uses the resulting diff and local check output to build merge evidence and Codex-friendly repair prompts | Does not call Codex APIs or judge model quality |
| Claude Code | Human-operated coding agent workflow | Code changes and repair attempts | Uses the resulting diff and local check output to build merge evidence and Claude-friendly handoff text | Keeps Claude-specific behavior in adapter output |
| Cursor | AI-assisted editor workflow | Code changes and editor-side repair attempts | Adds deterministic pre-merge evidence around Cursor-produced changes | Cursor remains the editor |
| aider | Coding-agent workflow | Code changes from its own workflow | Fits after an aider change to record checks, review packets, and repair evidence | Does not replace or rank aider |
| OpenHands | Coding-agent workflow | Code changes or execution attempts from its own workflow | Fits after an OpenHands change to preserve deterministic merge evidence | Does not replace or rank OpenHands |
| Goose | Coding-agent workflow | Code changes or execution attempts from its own workflow | Fits after a Goose change to preserve deterministic merge evidence | Does not replace or rank Goose |
| Semgrep | Static-analysis engine | Findings and SARIF-ready security evidence | QA-Z runs, records, normalizes, and reports Semgrep-backed deep evidence | Does not replace Semgrep rules or analysis |
| CI/test tools | Deterministic gate execution | Exit codes, logs, and artifacts | QA-Z assembles those checks into reviewable fast/deep evidence | Does not weaken configured gates |
| Human reviewer | Merge ownership | Review judgment and final decision | QA-Z supplies evidence, repair context, and verification comparison before merge | Does not replace human review |
| QA-Z | Local QA control plane | Contracts, checks, artifacts, repair prompts, and verification reports | Sits around coding agents as model-agnostic merge evidence | Does not edit code or perform live agent execution |

## Why Not Just Tests?

Tests are necessary, but they do not explain the agent change, assemble a contract, produce a repair packet, or compare baseline and candidate run evidence.

QA-Z keeps ordinary tools in the loop:

- `ruff`, `pytest`, `mypy`, `eslint`, `tsc`, and `vitest` remain deterministic fast gates.
- Semgrep remains the deep static-analysis engine.
- QA-Z records the evidence, renders review packets, and tells the next agent or human what to fix.

## Why Not Just A Coding Agent?

Coding agents can write code quickly, but their success claims are not merge evidence.

QA-Z answers the merge question:

```text
AI-generated code -> QA-Z -> deterministic merge evidence
```

Use the agent to write the change. Use QA-Z before you merge it.

## When To Use QA-Z With These Tools

Use QA-Z:

- after an agent changes code;
- before merging generated or AI-assisted code;
- when a repair prompt must be evidence-backed;
- when a candidate fix must be compared against a baseline;
- when CI should preserve fast/deep artifacts before human review.

## What QA-Z Does Not Claim

- no live model API execution.
- no autonomous editing.
- no package publishing claim.
- no hosted automation claim.
- no branch mutation, commits, pushes, tags, releases, deploys, or bot comments.
- no replacement for tests, Semgrep, or human review.
- no ranking, benchmark, or model-quality superiority claim.
