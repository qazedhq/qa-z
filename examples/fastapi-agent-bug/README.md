# FastAPI Agent Bug Demo

AI wrote a bad FastAPI auth check. QA-Z caught it.

This runnable demo mirrors the five-minute safety-belt story with a FastAPI-shaped app. It keeps the test surface dependency-light by testing pure functions directly; if FastAPI is installed, `app/main.py` also exposes a small app object.

## Baseline

```bash
qa-z plan --title "FastAPI auth check caught by QA-Z" --issue issue.md --spec spec.md --slug fastapi-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Expected: `py_test` fails because a non-owner can read another user's invoice. Semgrep flags the risky `return user_id is not None` flow.

## Candidate

```bash
cp app/main.fixed.py app/main.py
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

PowerShell:

```powershell
Copy-Item app\main.fixed.py app\main.py -Force
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

The demo does not call live agents or mutate branches.
