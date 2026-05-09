# Demo Visual Asset

Status: the README now uses a checked-in terminal cast and SVG visual. No GIF is committed in this package; if a GIF is added later, it must be generated from the checked-in casts below.

Checked-in sources:

- [../assets/qa-z-demo.cast](../assets/qa-z-demo.cast)
- [../assets/qa-z-demo.svg](../assets/qa-z-demo.svg)
- [../assets/qa-z-agent-auth-bug.cast](../assets/qa-z-agent-auth-bug.cast)

README scenario:

```bash
pipx install git+https://github.com/qazedhq/qa-z.git
qa-z init --profile python --with-agent-templates
qa-z doctor
qa-z demo auth-bug
qa-z guard --from-run latest --adapter codex
qa-z repair-prompt --from-run latest --adapter codex
```

Full agent-auth-bug cast scenario:

```bash
qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Acceptance status:

- README links to the short SVG visual and terminal cast without replacing text commands.
- The asset is deterministic and public-safe.
- The full agent-auth-bug cast shows deterministic QA-Z evidence, not live-agent execution.
- Examples documentation links the cast proof and keeps runnable versus placeholder labels explicit.
- Local machine paths, secrets, and private artifacts are not visible.
- A future GIF is optional, not required to close the current visual proof issues.

Validation:

```bash
python -m pytest -q tests/test_launch_growth_package.py tests/test_public_docs_current_truth.py
```
