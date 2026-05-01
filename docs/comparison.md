# QA-Z Comparison

QA-Z is not a coding agent. It is the deterministic QA layer around coding agents.

| Tool | Writes code | Runs checks | Produces repair prompt | Verifies repair | Model-agnostic QA evidence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Codex | yes | partial | partial | partial | no |
| Claude Code | yes | partial | partial | partial | no |
| Cursor | yes | partial | partial | partial | no |
| Semgrep | no | yes | no | no | partial |
| pytest/ruff/mypy | no | yes | no | no | no |
| QA-Z | no | yes | yes | yes | yes |

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
