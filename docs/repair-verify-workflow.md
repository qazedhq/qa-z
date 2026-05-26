# Repair -> Verify Workflow

Use this workflow after QA-Z blocks a change and writes a repair prompt. It keeps
the loop deterministic: QA-Z prepares the evidence and verifies the result, but a
human or external executor applies the code fix.

```text
qa-z guard
-> do_not_merge / needs_review
-> qa-z repair-prompt
-> apply the fix outside QA-Z
-> qa-z verify
-> improved / unchanged / regressed / mixed / verification_failed
```

## Short Loop

From a repository that already has a failed or risky latest run:

```bash
qa-z guard --from-run latest --adapter codex
qa-z repair-prompt --from-run latest --adapter codex
qa-z verify --from-run latest
```

`qa-z verify --from-run latest` treats the selected run as the baseline and
reruns fast evidence plus comparable deep evidence into `.qa-z/runs/candidate`
before comparing. Use this after the repair has already been applied to the
working tree.

The command writes:

- `.qa-z/runs/candidate/verify/summary.json`
- `.qa-z/runs/candidate/verify/compare.json`
- `.qa-z/runs/candidate/verify/report.md`

JSON output keeps the compare schema and adds CLI pointers:

```bash
qa-z verify --from-run latest --json
```

The JSON includes `kind`, `verdict`, `baseline`, `candidate`, `summary`,
`fast_checks`, `deep_findings`, `artifacts`, and `next_actions`.

## Explicit Baseline/Candidate Mode

The existing explicit comparison mode remains supported when the candidate run
already exists:

```bash
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Use explicit mode when CI or another script already produced comparable
candidate artifacts.

## Read The Result

- `improved`: blockers decreased and no new blockers appeared.
- `unchanged`: the repair did not materially change the blocking evidence.
- `regressed`: the candidate is worse. Human output labels this as
  `worse (regressed)`.
- `mixed`: some blockers resolved, but new or remaining issues need review.
- `verification_failed`: evidence was missing, invalid, or not comparable.

Only `improved` exits with code `0`. Other verdicts are still useful evidence
for the next repair pass.

## Auth-Bug Demo

The packaged demo has a deterministic fixed file:

```bash
qa-z demo auth-bug
cd .qa-z/demo/auth-bug
qa-z guard --from-run latest --adapter codex
qa-z repair-prompt --from-run latest --adapter codex
cp app/auth.fixed.py app/auth.py
qa-z verify --from-run latest --config qa-z.demo.yaml
```

PowerShell:

```powershell
qa-z demo auth-bug
Set-Location .qa-z\demo\auth-bug
qa-z guard --from-run latest --adapter codex
qa-z repair-prompt --from-run latest --adapter codex
Copy-Item app\auth.fixed.py app\auth.py -Force
qa-z verify --from-run latest --config qa-z.demo.yaml
```

The expected verify verdict is `improved`.

## Boundaries

This workflow does not call live model APIs, run an external agent, silently edit
target repositories, create branches, commit, push, deploy, publish packages, or
post GitHub comments. Generated `.qa-z/**` runtime evidence stays local unless a
small fixture or proof packet is intentionally frozen and reviewed.
