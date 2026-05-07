# AGENTS.md

## Mission

Build QA-Z as a Codex-first, model-agnostic QA control plane for coding agents.

The repository should always bias toward:

- executable quality gates over vague advice
- explicit contracts over implied requirements
- deterministic evidence over stylistic guesswork
- repairable feedback over raw failure dumps

## Repository expectations

- Keep the public README aligned with the actual implementation state.
- Preserve the core command names: `init`, `plan`, `fast`, `deep`, `review`, `repair-prompt`.
- Prefer small, composable modules over large framework-heavy abstractions.
- Treat Codex and Claude integrations as adapters, not the core engine.
- Do not claim deep QA automation exists unless the runners and tests actually prove it.

## Working agreements

- Write tests before adding behavior to Python code.
- Run `python -m pytest` after modifying Python sources or tests.
- If CLI behavior changes, update both tests and README examples.
- Keep `qa-z.yaml.example` in sync with any config surface changes.
- When adding workflows or agent templates, favor deterministic gates and explicit permissions.

## Documentation rules

- Update `docs/mvp-issues.md` when roadmap scope materially changes.
- Put design and planning artifacts under `docs/superpowers/`.
- Call out bootstrap placeholders honestly in docs and CLI output.

## Default task loop

1. Confirm the task is about QA-Z and identify the affected surface: CLI, planner, adapters, artifacts, benchmark, repair, docs, or release.
2. Run skill selection before implementation: Superpowers first, Matt Pocock for task routing, Karpathy Guidelines for coding discipline, then any repo-specific workflow implied by the touched surface.
3. Preserve deterministic QA gates and write tests before changing Python behavior.
4. Keep Codex and Claude logic behind adapters; do not move agent-specific behavior into the core planner.
5. Run the smallest relevant pytest/mypy/ruff or CLI verification and report exact evidence.

## Matt Pocock Skills

- Treat the installed Matt Pocock skills as a Codex-first execution accelerator after these repository rules.
- Every meaningful task must explicitly decide whether a Matt Pocock skill applies; use the smallest applicable skill set.
- Skill routing:
  - new feature, unclear scope, terminology alignment, or decision capture -> `grill-with-docs`
  - bug, regression, failing check, or performance issue -> `diagnose`
  - behavior-changing Python or CLI code -> `tdd`
  - unfamiliar subsystem or broad context request -> `zoom-out`
  - architecture cleanup or module-boundary improvement -> `improve-codebase-architecture`
  - PRD or issue generation -> `to-prd` or `to-issues`
  - issue intake or label movement -> `triage`
  - reusable workflow capture -> `write-a-skill`
- Repo configuration:
  - Issue tracker: GitHub Issues for `qazedhq/qa-z`. See `docs/agents/issue-tracker.md`.
  - Triage labels: default five-role vocabulary. See `docs/agents/triage-labels.md`.
  - Domain docs: single-context by default, using `README.md`, `docs/`, and any future `CONTEXT.md` or ADRs. See `docs/agents/domain.md`.
- If a Matt Pocock skill conflicts with these repository rules, deterministic QA-Z gates, explicit user instructions, or current repo evidence, follow the higher-priority instruction and state the adaptation.

## Karpathy Guidelines

- Use `karpathy-guidelines` as the default coding-discipline layer for non-trivial implementation, review, refactor, and debugging work.
- Apply it with Matt Pocock skills: Matt Pocock chooses the workflow; Karpathy keeps the execution simple, surgical, explicit about assumptions, and tied to verifiable success criteria.
- Before coding, state assumptions or ask when ambiguity could change the safe implementation.
- Prefer the simplest implementation that satisfies the request; do not add speculative abstractions, features, configurability, or dependencies.
- Touch only files and lines needed for the task; mention unrelated cleanup instead of editing it.
- Define success criteria and run targeted verification before claiming completion.
- For QA-Z, preserve deterministic gates, CLI contracts, adapter boundaries, and repairable evidence outputs unless the task explicitly changes them.

## Safety rails

- Never replace deterministic pass/fail checks with LLM-only judgments.
- Never add hidden network dependencies to local QA flows without documenting them.
- Never introduce agent-specific logic into the core planner if it belongs in `adapters/`.

## Useful commands

```bash
python -m pip install -e .[dev]
python -m pytest
python -m qa_z --help
python -m qa_z init
```
