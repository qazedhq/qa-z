# Hosted Demo Plan

QA-Z does not need a cloud product to have a hosted demo.

## Demo Shape

- Static docs page with embedded `docs/assets/qa-z-agent-auth-bug.cast`.
- Downloadable or browsable `examples/agent-auth-bug` fixture.
- Copy/paste commands for local replay.
- No live model calls, live-agent execution, or uploaded source code.
- No QA-Z Cloud claim; the page is static documentation for a local workflow.

## 3-Minute Video Outline

1. AI agent changes auth logic.
2. QA-Z generates a contract.
3. Fast checks fail.
4. Semgrep flags the risky flow.
5. QA-Z produces a Codex repair prompt.
6. Candidate fix passes.
7. `qa-z verify` reports `improved`.

## Local Replay Contract

The hosted page should name the exact local inputs and outputs required to recreate the demo:

```bash
cd examples/agent-auth-bug
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
cp app/main.fixed.py app/main.py
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Replay artifacts are the checked-in fixture, `.qa-z/runs/baseline`, `.qa-z/runs/candidate`, the verification report, and the asciinema cast under `docs/assets/qa-z-agent-auth-bug.cast`.

## Hosted Demo Acceptance

- Demo can be replayed locally from `examples/agent-auth-bug`.
- Video and asciinema show the same command spine.
- No claim depends on hidden cloud state, QA-Z Cloud, or live-agent execution.
- The static page links to the fixture, commands, and artifacts needed to recreate the demo.
