# QA-Z Quickstart

This quickstart gets from install to deterministic QA evidence in about five minutes.

## Install

Install the current public alpha from GitHub:

```bash
pipx install "git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha"
```

Or with uv:

```bash
uv tool install "git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha"
```

Contributor fallback from this repository:

```bash
python -m pip install -e .[dev]
```

Install Semgrep when running deep checks:

```bash
python -m pip install semgrep
```

## Run The 60-Second Packaged Demo

Start with the packaged auth-bug demo before adapting QA-Z to your own repository:

```bash
qa-z demo auth-bug
cd .qa-z/demo/auth-bug
qa-z guard --from-run latest --adapter codex
qa-z repair-prompt --from-run latest --adapter codex
```

The guard is expected to block the change. That is the point: QA-Z turns the risky agent edit into deterministic evidence and a repair handoff.

Use `qa-z demo auth-bug --json` when scripts or docs validators need the demo
root, guard verdict path, repair prompt path, and follow-up commands as one
machine-readable payload.

## Run The Example Repository Demo

For deeper fast/deep/review artifacts from a source checkout:

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

Expected result: `qa-z verify` reports verdict `improved` with resolved blockers and no regressions.

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

Use `qa-z doctor --json` when automation needs structured config or onboarding errors, and use `qa-z doctor --strict` when warnings such as missing agent instruction templates should fail a handoff gate.
`doctor` also fails before execution on malformed check definitions, including
empty check kinds and malformed Semgrep policy fields.

The starter GitHub workflow installs the public alpha, then runs `qa-z doctor --json` before `qa-z fast --json` with read-only repository contents permission.

Root `.qa-z/**` evidence is local by default. Commit source, tests, docs, and intentional fixtures, not incidental local runs.
