# QA-Z Quickstart

This quickstart gets from install to deterministic QA evidence in about five minutes.

## Install

Install the current public alpha from GitHub:

```bash
pipx install "git+https://github.com/qazedhq/qa-z.git@v0.9.8-alpha"
```

Or with uv:

```bash
uv tool install "git+https://github.com/qazedhq/qa-z.git@v0.9.8-alpha"
```

Contributor fallback from this repository:

```bash
python -m pip install -e .[dev]
```

Install Semgrep when running deep checks:

```bash
python -m pip install semgrep
```

## Run The Demo

```bash
cd examples/agent-auth-bug
qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

The baseline run is expected to fail. That is the point: QA-Z catches an unsafe auth change and turns the failure into a repair packet.

## Verify A Repair

From the demo directory, replace the bad implementation with the fixed one and compare the run artifacts:

```bash
cp app/auth.fixed.py app/auth.py
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

On Windows PowerShell, use:

```powershell
Copy-Item app\auth.fixed.py app\auth.py -Force
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

## Use It In Your Repository

```bash
qa-z init --profile python --with-agent-templates --with-github-workflow
qa-z doctor
qa-z plan --title "Review recent agent change" --slug agent-change --overwrite
qa-z fast
qa-z deep --from-run latest
qa-z review --from-run latest
qa-z repair-prompt --from-run latest --adapter codex
```

If `qa-z` is not on PATH, use `python -m qa_z` for the same commands.

Root `.qa-z/**` evidence is local by default. Commit source, tests, docs, and intentional fixtures, not incidental local runs.
