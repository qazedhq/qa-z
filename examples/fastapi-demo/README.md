# FastAPI Demo

This dependency-light demo shows the QA-Z alpha loop against a small FastAPI-shaped Python service.

The service exposes pure functions so the demo works without installing a web server. If `fastapi` is installed, `app/main.py` also creates a real `FastAPI` app.

It is a deterministic fast and repair-prompt demo. It does not configure deep checks, does not call live agents, and does not run `repair-session`, `executor-bridge`, or `executor-result`.

## Passing Flow

From this directory:

```bash
python -m qa_z init --path .
python -m qa_z plan --path . --title "Protect invoice access" --issue issue.md --spec spec.md
python -m qa_z fast --path . --output-dir .qa-z/runs/pass
python -m qa_z review --path . --from-run .qa-z/runs/pass
python -m qa_z repair-prompt --path . --from-run .qa-z/runs/pass
```

The passing run executes:

- `ruff check app example_tests`
- `ruff format --check app example_tests`
- `python -m pytest -q example_tests/app_example.py`

## Failing Repair Flow

The failing config runs a test against `app/buggy_main.py` to show the repair packet shape:

```bash
python -m qa_z fast --path . --config qa-z.failing.yaml --output-dir .qa-z/runs/fail
python -m qa_z review --path . --from-run .qa-z/runs/fail
python -m qa_z repair-prompt --path . --from-run .qa-z/runs/fail
```

Expected artifacts:

```text
.qa-z/runs/pass/fast/summary.json
.qa-z/runs/pass/fast/summary.md
.qa-z/runs/fail/fast/summary.json
.qa-z/runs/fail/repair/packet.json
.qa-z/runs/fail/repair/prompt.md
```

The failing run is intentional. It gives reviewers and coding agents concrete deterministic evidence instead of a vague instruction to "fix auth."
