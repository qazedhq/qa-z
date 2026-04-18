## Summary

-

## Validation

- [ ] `python -m ruff format --check .`
- [ ] `python -m ruff check .`
- [ ] `python -m mypy src tests`
- [ ] `python -m pytest`
- [ ] `python -m qa_z fast --selection smart --json`
- [ ] `python -m qa_z deep --selection smart --json`
- [ ] `python -m qa_z benchmark --json`

## Evidence

List the relevant deterministic artifacts or reports:

-

## Generated Artifact Policy

- [ ] I did not commit root `.qa-z/**`.
- [ ] I did not commit `benchmarks/results/work/**`.
- [ ] I did not commit `benchmarks/results/summary.json` or `benchmarks/results/report.md` unless this PR intentionally freezes generated evidence with context.
- [ ] Any fixture-local `.qa-z/**` evidence is under `benchmarks/fixtures/**/repo/.qa-z/**`.

## Boundaries

- [ ] This PR does not add live Codex, Claude, or other model execution.
- [ ] This PR does not replace deterministic checks with LLM-only judgment.
- [ ] This PR does not add hidden network dependencies to local QA flows.
- [ ] Agent-specific behavior is isolated to adapters or templates.
