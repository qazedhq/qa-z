# Contributing to QA-Z

QA-Z is a Codex-first, model-agnostic QA control plane. Contributions should keep the project biased toward executable quality gates, explicit contracts, deterministic evidence, and repairable feedback.

## Local Setup

```bash
python -m pip install -e .[dev]
```

## Required Validation

Run the Python gate before opening a pull request:

```bash
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest
```

Run the QA-Z release gate when a change touches CLI behavior, artifacts, workflows, benchmark fixtures, or public docs:

```bash
python -m qa_z fast --selection smart --json
python -m qa_z deep --selection smart --json
python -m qa_z benchmark --json
```

CLI behavior changes must update tests and README examples together. Config surface changes must keep `qa-z.yaml.example` aligned.

## Generated Artifact Policy

Do not commit root `.qa-z/**`, `benchmarks/results/work/**`, `benchmarks/results/summary.json`, or `benchmarks/results/report.md` unless a release task explicitly freezes generated evidence with surrounding context.

Fixture-local evidence under `benchmarks/fixtures/**/repo/.qa-z/**` is allowed when it is part of a deterministic benchmark vector.

See `docs/generated-vs-frozen-evidence-policy.md` for the full local by default versus intentional frozen evidence policy.

## Boundaries

QA-Z does not call live Codex, Claude, or other model APIs in local QA flows. Do not replace deterministic pass/fail checks with LLM-only judgments, and do not add hidden network dependencies to local gates.

Keep Codex and Claude behavior in adapters or templates; the core planner and runners should stay model-agnostic.
