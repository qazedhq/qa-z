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
