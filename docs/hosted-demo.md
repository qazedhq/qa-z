# Hosted Demo Plan

QA-Z does not need a cloud product to have a hosted demo.

## Demo Shape

- A static docs page with embedded asciinema.
- Downloadable example repository.
- Copy/paste commands for local replay.
- No live model calls.
- No uploaded source code.

## Static Page Boundary

The hosted demo is a static docs page, not QA-Z Cloud.

It must not imply QA-Z Cloud, hidden backend state, live-agent execution, or uploaded source-code analysis.

It must not:

- accept uploaded source code;
- run QA-Z on a remote backend;
- call live Codex, Claude, or other model APIs;
- store repository state;
- imply that repairs run on a hosted service;
- imply package publishing, deploy, branch mutation, or bot comments.

## Local Replay Source

The hosted demo must be replayable from:

```text
examples/agent-auth-bug
```

Use the canonical command spine from `docs/demo-script.md`.

```bash
python -m pip install -e .[dev]
python -m qa_z --help
cd examples/agent-auth-bug

qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex

python -m pip install semgrep
qa-z deep --from-run .qa-z/runs/baseline

cp app/auth.fixed.py app/auth.py
qa-z verify --from-run .qa-z/runs/baseline
```

PowerShell copy equivalent:

```powershell
Copy-Item app\auth.fixed.py app\auth.py -Force
```

## Recreated Demo Artifacts

A successful local replay should produce or reference:

```text
.qa-z/runs/baseline/fast/summary.json
.qa-z/runs/baseline/review/
.qa-z/runs/baseline/repair/
.qa-z/runs/baseline/deep/results.sarif
.qa-z/runs/candidate/fast/summary.json
.qa-z/runs/candidate/verify/summary.json
.qa-z/runs/candidate/verify/compare.json
.qa-z/runs/candidate/verify/report.md
```

Expected verification result: verdict `improved` with resolved blockers and no regressions.

## Static Assets

The hosted demo page can embed or link to:

- `docs/assets/qa-z-agent-auth-bug.cast`
- `docs/assets/qa-z-demo.cast`
- `docs/assets/qa-z-demo.svg`
- `docs/demo-script.md`

These assets are checked into the repository and should not depend on hidden hosted state.

## 3-Minute Video Outline

1. AI agent changes auth logic.
2. QA-Z generates a contract.
3. Fast checks fail.
4. Semgrep flags the risky flow.
5. QA-Z produces a Codex repair prompt.
6. Candidate fix passes.
7. `qa-z verify` reports `improved`.

## Hosted Demo Acceptance

- Demo can be replayed locally from `examples/agent-auth-bug`.
- Video and asciinema show the same command spine.
- The page links users back to local replay commands and expected artifacts.
- No claim depends on hidden backend state.
- No page copy implies QA-Z Cloud, live-agent execution, uploaded source-code analysis, package publishing, deploy, branch mutation, or bot comments.
