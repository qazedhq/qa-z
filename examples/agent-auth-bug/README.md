# Agent Auth Bug Demo

AI wrote a bad auth change. QA-Z caught it.

This five-minute demo shows QA-Z turning an unsafe invoice authorization change into deterministic repair evidence.

The demo does not call live agents, does not edit code autonomously, and does not require a web server. It uses local Python functions, pytest, ruff, and an optional Semgrep rule.

## Baseline: bad agent change

```bash
qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Expected result: `qa-z fast` fails because `tests/test_auth.py` proves a non-owner can view another user's invoice.

## Optional deep check

Install Semgrep first:

```bash
python -m pip install semgrep
qa-z deep --from-run .qa-z/runs/baseline
```

The local rule in `semgrep-rules/auth-bypass.yml` flags the risky `return actor_id is not None` pattern.

## Candidate repair and verification

Apply the included fixed implementation, rerun the gate, and compare:

```bash
cp app/auth.fixed.py app/auth.py
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

PowerShell:

```powershell
Copy-Item app\auth.fixed.py app\auth.py -Force
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

This is the core QA-Z story:

```text
AI-generated code -> QA-Z -> deterministic merge evidence
```
