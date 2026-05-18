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

## FastAPI Evidence Tour

After the baseline commands, inspect these local artifacts:

- `.qa-z/runs/baseline/fast/summary.json`
- `.qa-z/runs/baseline/deep/summary.json`
- `.qa-z/runs/baseline/deep/checks/sg_scan.json`
- `.qa-z/runs/baseline/deep/results.sarif`
- `.qa-z/runs/baseline/repair/codex.md`

Expected baseline evidence:

- baseline fast evidence fails because the non-owner invoice access test still fails.
- baseline deep evidence records 2 auth findings from `semgrep-rules/auth-bypass.yml`.
- repair prompt points at the owner-check problem and the FastAPI auth helper.

After copying `app/main.fixed.py` over `app/main.py` and running the
candidate commands, inspect these local artifacts:

- `.qa-z/runs/candidate/fast/summary.json`
- `.qa-z/runs/candidate/deep/summary.json`
- `.qa-z/runs/candidate/verify/summary.json`
- `.qa-z/runs/candidate/verify/compare.json`
- `.qa-z/runs/candidate/verify/report.md`

Expected candidate evidence:

- candidate fast and deep evidence pass after the fixed owner check is in place.
- fixed-file Semgrep scans report 0 findings for `app/main.fixed.py`.
- verification verdict is `improved`.
- `compare.json` is the machine-readable source of truth for the verdict.
- `repair_improved` is `true` in `verify/summary.json`.

Generated `.qa-z/**` files are local runtime evidence. Do not commit generated
`.qa-z` runtime evidence.
