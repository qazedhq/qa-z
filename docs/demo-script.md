# QA-Z demo script

This script shows the shortest path from a code change to QA evidence. It uses real CLI commands and does not depend on screenshots, GIFs, or generated media.

## Setup

```bash
python -m pip install -e .[dev]
python -m qa_z --help
python -m qa_z init --profile python --with-agent-templates --with-github-workflow
python -m qa_z doctor
python -m qa_z plan --title "Review recent agent change" --slug agent-change --overwrite
```

## Generate QA evidence

```bash
python -m qa_z fast
python -m qa_z deep --from-run latest
python -m qa_z review --from-run latest
python -m qa_z repair-prompt --from-run latest --adapter codex
```

## Verify a candidate repair

After an external repair tool or human applies a candidate fix, rerun the checks into a candidate run directory and compare it with the baseline evidence:

```bash
python -m qa_z verify \
  --baseline-run .qa-z/runs/baseline \
  --candidate-run .qa-z/runs/candidate
```

## Expected artifact surfaces

```text
.qa-z/runs/
.qa-z/runs/latest/review/
.qa-z/runs/latest/repair/
.qa-z/runs/latest/deep/results.sarif
.qa-z/sessions/
```

The TypeScript demo under [examples/typescript-demo/](../examples/typescript-demo/) is the quickest runnable example for a fast-gate walkthrough.
