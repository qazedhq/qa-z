# QA-Z Comparison

QA-Z is not a coding agent. It is the deterministic QA layer around coding agents.

## 30-second Positioning

- Codex/Cursor/aider/OpenHands = code generation and editing.
- Semgrep/CI = checks.
- QA-Z = merge evidence, repair prompt, and verify verdict.
- QA-Z complements human review and existing tools; it does not replace them.

| Tool | Primary job | Writes code | Runs checks | Produces repair prompt | Verifies repair | Model-agnostic QA evidence |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Codex | agentic code changes | yes | partial | partial | partial | no |
| Cursor | editor-native AI changes | yes | partial | partial | partial | no |
| Claude Code | agentic code changes | yes | partial | partial | partial | no |
| aider | repository editing loop | yes | partial | partial | partial | no |
| OpenHands | autonomous development workflow | yes | partial | partial | partial | no |
| GitHub Copilot | editor and PR assistance | yes | partial | partial | partial | no |
| Semgrep | static-analysis rules | no | yes | no | no | partial |
| pytest/ruff/mypy/CI | deterministic checks | no | yes | no | no | no |
| QA-Z | merge evidence and repair handoff | no | yes | yes | yes | yes |

## How QA-Z Relates To Semgrep And CI

QA-Z is not a Semgrep wrapper.

Semgrep and CI tools remain the deterministic engines that find specific issues. QA-Z records those results alongside fast checks, summary output, repair prompts, guard decisions, and post-repair verification evidence.

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

## Human Review Still Matters

QA-Z prepares the evidence a reviewer needs: what changed, what failed, why it matters, how to repair it, and whether the repair improved the candidate run. A human still decides whether the product behavior is right for the repository.
