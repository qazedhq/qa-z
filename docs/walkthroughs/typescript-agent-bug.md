# Walkthrough: TypeScript Agent Bug Caught By QA-Z

This walkthrough uses
[../../examples/typescript-agent-bug/](../../examples/typescript-agent-bug/).
It shows the baseline failure, candidate owner-check fix, and `qa-z verify`
comparison for a TypeScript-shaped authorization bug.

The example is local and dependency-light. It runs local Node scripts and the
checked-in Semgrep rule. It does not invoke live agent APIs, package registries,
hosted services, or network APIs.
No live agents are invoked.

## 1. What this walkthrough proves

QA-Z can package deterministic repair evidence for a mixed-language code path:

- fast checks catch the failing TypeScript authorization test;
- deep checks record the TypeScript auth-bypass Semgrep finding;
- repair prompt output gives an external executor or human the missing owner
  check;
- candidate evidence proves the fixed source passes;
- `qa-z verify` reports whether the candidate improved the baseline evidence.

## 2. Baseline bug

The unsafe implementation in `src/invoice.ts` rejects anonymous users but then
returns `actorId !== null`. That means any signed-in user can view any invoice,
even when `invoice.ownerId` belongs to someone else.

The fixed source in `src/invoice.fixed.ts` preserves the admin and anonymous
branches, then returns `actorId === invoice.ownerId`.

## 3. Baseline commands

Run from `examples/typescript-agent-bug/`:

```bash
qa-z plan --title "TypeScript agent bug caught by QA-Z" --issue issue.md --spec spec.md --slug typescript-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Expected baseline evidence:

- `ts_test` fails because a non-owner can view another user's invoice.
- `sg_scan` records `qa-z.typescript-auth-bypass-any-signed-in-user`.
- `repair/codex.md` points at the missing `actorId === invoice.ownerId`
  owner check.

## 4. Baseline artifacts to inspect

After the baseline commands, inspect:

- `.qa-z/runs/baseline/fast/summary.json`: fast check status, including the
  `ts_test` failure.
- `.qa-z/runs/baseline/deep/summary.json`: deep check outcome and blocking
  finding count.
- `.qa-z/runs/baseline/deep/checks/sg_scan.json`: raw Semgrep JSON captured
  for the configured `sg_scan` check.
- `.qa-z/runs/baseline/deep/results.sarif`: SARIF representation of the
  TypeScript auth-bypass finding.
- `.qa-z/runs/baseline/repair/codex.md`: executor-facing repair prompt built
  from the recorded baseline evidence.

## 5. Candidate fix

Copy the fixed source over the unsafe source:

```bash
cp src/invoice.fixed.ts src/invoice.ts
```

PowerShell:

```powershell
Copy-Item src\invoice.fixed.ts src\invoice.ts -Force
```

The candidate source should now compare the actor identity to the invoice owner:

```typescript
return actorId === invoice.ownerId;
```

## 6. Candidate commands

Run the same evidence path for the candidate:

```bash
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Expected candidate evidence:

- candidate fast checks pass;
- candidate deep checks pass with no remaining TypeScript auth-bypass finding;
- `qa-z verify` writes verification artifacts under the candidate run.

## 7. Verification artifacts to inspect

After the candidate and verification commands, inspect:

- `.qa-z/runs/candidate/fast/summary.json`: fixed candidate fast evidence.
- `.qa-z/runs/candidate/deep/summary.json`: fixed candidate deep evidence.
- `.qa-z/runs/candidate/verify/summary.json`: compact verdict and counts.
- `.qa-z/runs/candidate/verify/compare.json`: machine-readable comparison of
  resolved, remaining, new, regressed, and not-comparable evidence.
- `.qa-z/runs/candidate/verify/report.md`: human-readable verification report
  for review and handoff.

## 8. Verdict interpretation

Expected verdict: `improved`.

`improved` means the candidate reduced baseline blockers without introducing
new regressions. If verification reports `mixed`, `regressed`, `unchanged`, or
`verification_failed`, inspect `compare.json` first because it is the
machine-readable source of truth for the comparison.

## 9. Generated artifact policy

Generated `.qa-z/**` files are local runtime evidence. Do not commit generated
`.qa-z` runtime evidence from this walkthrough.

Commit source, documentation, tests, or intentionally reviewed frozen fixtures
only. Keep local baseline and candidate runs out of the source tree unless a
maintainer explicitly asks for a frozen evidence fixture.

## 10. No live-agent / no network boundary

This walkthrough stays inside local source files, local Node scripts, QA-Z
artifact writers, and the checked-in Semgrep rule. It does not publish packages,
create tags or releases, deploy, mutate branches, post GitHub comments, call
hosted model APIs, or require hosted services.
