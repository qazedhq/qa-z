# Walkthrough: AI Auth Bug Caught By QA-Z

This walkthrough uses [../../examples/agent-auth-bug/](../../examples/agent-auth-bug/) and [../../examples/fastapi-agent-bug/](../../examples/fastapi-agent-bug/). Both are local deterministic examples; neither calls live agents, hosted services, or package registries.

## Python Auth Baseline

```bash
qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Expected: the baseline fast gate fails because a non-owner can view another user's invoice, and Semgrep reports 2 findings for the signed-in-user shortcut plus the missing owner check.

## Python Auth Candidate

```bash
cp app/auth.fixed.py app/auth.py
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Expected: candidate fast/deep gates pass and verification verdict is `improved`.

## FastAPI Auth Baseline

Run from `examples/fastapi-agent-bug`:

```bash
qa-z plan --title "FastAPI auth check caught by QA-Z" --issue issue.md --spec spec.md --slug fastapi-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Expected: `py_test` fails because a non-owner can read another user's invoice.
Semgrep reports 2 findings from
`semgrep-rules/auth-bypass.yml`: the signed-in-user shortcut and
`qa-z.fastapi-auth-bypass-missing-owner-check`.

## FastAPI Auth Candidate

```bash
cp app/main.fixed.py app/main.py
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Expected: fixed candidate checks pass, fixed-file Semgrep scans report 0
findings, and `qa-z verify` reports `improved`.

QA-Z writes local artifacts under `.qa-z/runs/baseline` and
`.qa-z/runs/candidate`. Do not commit generated `.qa-z` runtime evidence.
