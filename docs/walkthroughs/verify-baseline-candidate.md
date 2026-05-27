# Verify Baseline/Candidate Workflow

This walkthrough shows two `qa-z verify` modes: the short repair loop that reruns
candidate evidence from a baseline, and the explicit comparison loop for an
existing baseline run and an existing repaired candidate run:

```text
baseline run
-> repair-prompt
-> candidate run
-> qa-z verify
-> verify/summary.json
-> verify/compare.json
-> verify/report.md
-> improved / mixed / regressed / unchanged / verification_failed
```

## 1. What verify proves

`qa-z verify` answers one narrow question: did the candidate run improve the
baseline evidence? It compares recorded fast and deep artifacts, writes
verification artifacts, and returns a deterministic verdict.

Verification is deterministic and does not rely on LLM-only judgment. It does
not edit code, call Codex or Claude APIs, run an external executor, create
branches, commit, push, deploy, or post GitHub comments.

By default, the verification artifacts are written under the candidate run:

```text
.qa-z/runs/candidate/verify/summary.json
.qa-z/runs/candidate/verify/compare.json
.qa-z/runs/candidate/verify/report.md
```

## 2. Baseline run

Start from the repository state before the repair. The baseline must preserve
the failing or risky evidence that the repair prompt will address.

```bash
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

Inspect or hand off these baseline artifacts:

- `.qa-z/runs/baseline/fast/summary.json`: fast check status, executed commands,
  exit codes, and stdout/stderr tails.
- `.qa-z/runs/baseline/deep/summary.json`: deep finding evidence, policy, and
  Semgrep-derived blocking status when deep checks are configured.
- `.qa-z/runs/baseline/repair/codex.md`: deterministic repair prompt for the
  external Codex-style repair executor or a human operator.

The repair prompt is generated from existing run artifacts. It does not rerun
checks and it does not call a live model.

## 3. Candidate run

After a human or external executor applies the repair outside QA-Z, run the same
evidence path for the candidate state:

```bash
qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
```

Inspect these candidate artifacts before comparing:

- `.qa-z/runs/candidate/fast/summary.json`: post-repair fast evidence.
- `.qa-z/runs/candidate/deep/summary.json`: post-repair deep evidence.

Use comparable evidence on both sides. If the baseline has a deep summary but
the candidate does not, or the candidate has a deep summary but the baseline
does not, verification records that evidence as not comparable and returns
`verification_failed`.

## 4. Run qa-z verify

For the first-class repair loop, apply the repair and let verify create
candidate evidence:

```bash
qa-z verify --from-run .qa-z/runs/baseline
```

Compare the recorded baseline and candidate runs:

```bash
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

Use `python -m qa_z verify ...` when the console script is not on `PATH`.

`qa-z verify` exits successfully only for `improved`. Non-improved verdicts are
still useful evidence: they tell the maintainer whether the repair is incomplete,
worse, or not comparable.

## 5. Inspect artifacts

Read the generated verification artifacts in this order:

1. `.qa-z/runs/candidate/verify/summary.json`
2. `.qa-z/runs/candidate/verify/compare.json`
3. `.qa-z/runs/candidate/verify/report.md`

`summary.json` is the compact numeric outcome. It includes the final `verdict`,
`repair_improved`, blocker counts before and after, resolved count, new issue
count, regression count, and not-comparable count.

`compare.json` is the machine-readable source of truth. It groups fast checks
and deep findings into `resolved`, `still_failing`, `regressed`,
`newly_introduced`, and `skipped_or_not_comparable`.

`report.md` is the human-readable companion for reviews and handoffs. It
summarizes the verdict, aggregate counts, fast-check categories, deep-finding
categories, and the command shape needed to reproduce the comparison.

## 6. Interpret verdicts

- `improved` means the candidate reduced blockers without new regressions.
- `mixed` means some issues improved but new or remaining issues need review.
- `regressed` means the candidate is worse than the baseline.
- `unchanged` means the candidate did not materially improve the baseline.
- `verification_failed` means the comparison could not complete; rerun or inspect artifacts.

Treat `compare.json` as the final evidence for the verdict. Use `report.md` for
human review, but do not override the machine-readable comparison with an
LLM-only claim.

## 7. Common failure modes

- Missing baseline fast summary: rerun `qa-z fast --output-dir .qa-z/runs/baseline`.
- Missing candidate fast summary: rerun `qa-z fast --output-dir .qa-z/runs/candidate`.
- One-sided deep evidence: rerun `qa-z deep --from-run` for the missing side, or
  compare a fast-only baseline and candidate when neither side has deep evidence.
- Stale repair prompt: regenerate `qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex`.
- Unexpected `unchanged`: inspect `summary.json` for `resolved_count`, then use
  `compare.json` to find remaining blockers.
- Unexpected `mixed` or `regressed`: inspect `new_issue_count` and
  `regression_count`, then repair the newly introduced or regressed evidence
  before rerunning the candidate.
- `verification_failed`: inspect missing, invalid, or not-comparable artifacts,
  then rerun the command that owns the missing evidence.

## 8. Generated artifact policy

Generated root `.qa-z/**` stays local by default. Do not commit generated
`.qa-z/**` runtime evidence unless the artifact is intentionally frozen with context,
such as a small benchmark fixture or documented proof packet.

Do not commit generated `.qa-z/**` runtime evidence from this walkthrough. Commit
source, docs, tests, fixtures, or intentionally reviewed frozen evidence only.
