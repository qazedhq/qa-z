# FastAPI Agent Bug Demo

AI wrote a bad FastAPI auth check. QA-Z caught it.

This runnable demo mirrors the five-minute safety-belt story with a FastAPI-shaped app. It keeps the test surface dependency-light by testing pure functions directly; if FastAPI is installed, `app/main.py` also exposes a small app object.

## Terminal proof

The shared launch proof [qa-z-agent-auth-bug.cast](../../docs/assets/qa-z-agent-auth-bug.cast) shows the same evidence shape used here: `qa-z plan`, `qa-z fast`, `qa-z deep`, `qa-z repair-prompt`, and `qa-z verify`. This FastAPI example is runnable, not placeholder-only.

## Baseline

```bash
qa-z plan --title "FastAPI auth check caught by QA-Z" --issue issue.md --spec spec.md --slug fastapi-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Expected: `py_test` fails because a non-owner can read another user's invoice. Semgrep reports 2 findings: the risky `return user_id is not None` flow and the broader helper shape that rejects anonymous users without returning a `user_id == invoice.owner_id` owner check. QA-Z writes local evidence under `.qa-z/runs/baseline`. Do not commit generated `.qa-z` runtime evidence.

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

## Evidence checklist

After running the baseline and candidate commands, inspect:

- `.qa-z/runs/baseline/fast/summary.json`
- `.qa-z/runs/baseline/deep/summary.json`
- `.qa-z/runs/baseline/repair/codex.md`
- `.qa-z/runs/candidate/verify/summary.json`
- `.qa-z/runs/candidate/verify/report.md`

Expected: baseline fails, candidate passes, and verification reports `improved`.

Generated `.qa-z/**` files are local runtime evidence. Do not commit generated `.qa-z` runtime evidence.
