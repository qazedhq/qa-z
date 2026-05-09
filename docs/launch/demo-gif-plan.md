# Demo GIF Plan

The demo GIF should be generated from the checked-in asciinema cast, not from
hand-edited or fabricated terminal output.

Source:

- [../assets/qa-z-agent-auth-bug.cast](../assets/qa-z-agent-auth-bug.cast)

Scenario:

```bash
qa-z demo auth-bug
qa-z guard
qa-z repair-prompt --from-run latest --adapter codex
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Acceptance:

- The GIF is short enough for the README first screen.
- The GIF shows deterministic QA-Z evidence, not live-agent execution.
- The README keeps copyable text commands next to the visual.
- Local machine paths, secrets, and private artifacts are not visible.

Validation:

```bash
python -m pytest -q tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py
```
