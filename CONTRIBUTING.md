# Contributing to QA-Z

QA-Z is a Codex-first, model-agnostic QA control plane. Contributions should keep the project biased toward executable quality gates, explicit contracts, deterministic evidence, and repairable feedback.

## Local Setup

```bash
python -m pip install -e .[dev]
```

Install Semgrep when running the documented deep QA gate locally:

```bash
python -m pip install semgrep
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

## Good First Issues

Good first issues should be small, deterministic, and easy to verify locally.
Prefer tasks that improve examples, docs, fixtures, or CI evidence without
changing core planner behavior.

Strong candidates:

- add a screenshot or asciinema capture for `examples/agent-auth-bug`;
- improve the Semgrep rule in the auth-bug demo with a focused fixture;
- add a TypeScript auth-bug demo using Vitest;
- clarify `pipx` or `uv tool install` docs after a package publish;
- add a GitHub Actions summary screenshot or SARIF walkthrough.

Every issue should include the expected file paths, the validation command, and
the artifact or documentation surface that proves the work.

## Generated Artifact Policy

Do not commit root `.qa-z/**`, `benchmarks/results/work/**`, `benchmarks/results/summary.json`, or `benchmarks/results/report.md` unless a release task explicitly freezes generated evidence with surrounding context.

Fixture-local evidence under `benchmarks/fixtures/**/repo/.qa-z/**` is allowed when it is part of a deterministic benchmark vector.

See `docs/generated-vs-frozen-evidence-policy.md` for the full local by default versus intentional frozen evidence policy.

## Boundaries

QA-Z does not call live Codex, Claude, or other model APIs in local QA flows. Do not replace deterministic pass/fail checks with LLM-only judgments, and do not add hidden network dependencies to local gates.

Keep Codex and Claude behavior in adapters or templates; the core planner and runners should stay model-agnostic.
