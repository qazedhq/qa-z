# Evidence Summary

Run `qa-z summary --from-run latest` when QA-Z has produced artifacts and you
want the first page to read. It is a local evidence navigator for maintainers:
it does not rerun checks, call a model, repair code, post comments, publish
packages, create branches, push, deploy, or upload artifacts.

Use it after any of these flows:

- `qa-z guard --adapter codex --deep auto`
- `qa-z fast` followed by `qa-z deep --from-run latest`
- `qa-z repair-prompt --from-run latest --adapter codex`
- `qa-z verify --baseline-run latest --candidate-run <candidate-run>`

## Human Output

```bash
qa-z summary --from-run latest
```

The text output is intentionally short:

```text
QA-Z Summary: warning
Verdict: do_not_merge
Run: .qa-z/runs/baseline

Evidence:
PASS fast summary: failed (.qa-z/runs/baseline/fast/summary.json)
MISS deep summary: missing (.qa-z/runs/baseline/deep/summary.json)
MISS repair prompt: .qa-z/runs/baseline/repair/prompt.md
MISS verify report: .qa-z/runs/baseline/verify/report.md

Top risks:
1. fast:py_type - mypy exited with code 1.

Next actions:
1. Run `qa-z deep --from-run latest`
2. Run `qa-z repair-prompt --from-run latest --adapter codex`
```

`status` tells you whether the evidence set is complete enough to read:

- `passed`: summary artifacts are present and the recorded evidence is clear.
- `warning`: the command found a run, but some companion evidence is missing or
  stale, such as a missing deep summary.
- `failed`: the recorded fast, deep, or guard evidence contains failures or an
  error verdict.
- `missing`: no run evidence could be resolved.

`verdict` is the merge-facing outcome. If `guard/verdict.json` exists, summary
uses that guard verdict. Otherwise it derives a conservative verdict from fast
and deep summaries: failed fast or deep checks become `do_not_merge`, unsupported
fast checks become `needs_review`, and clean recorded evidence becomes
`merge_ok`.

## JSON Output

```bash
qa-z summary --from-run latest --json
```

The JSON shape is stable for automation:

- `status`
- `verdict`
- `run_dir`
- `evidence`
- `top_findings`
- `repair_prompt`
- `verify_report`
- `next_actions`
- `warnings`

Each evidence entry includes `path` and `exists`. Entries that have a recorded
status also include `status`.

## Markdown Output

```bash
qa-z summary --from-run latest --markdown --output .qa-z/runs/latest/summary.md
```

Use Markdown when you want a reviewable local artifact. Generated `.qa-z/**`
runtime evidence is local by default; do not commit it unless the repository has
explicitly frozen that evidence as a reviewed fixture or proof packet.

## Common Fixes

- No run exists: run `qa-z guard --adapter codex --deep auto`, or start with
  `qa-z demo auth-bug` in a new checkout.
- Latest manifest is stale: summary falls back to the newest
  `*/fast/summary.json` and warns about `latest-run.json`.
- Deep summary is missing: run `qa-z deep --from-run latest`.
- Repair prompt is missing after a blocking verdict: run
  `qa-z repair-prompt --from-run latest --adapter codex`.
- Verify report is missing after a repair prompt: run
  `qa-z verify --baseline-run latest --rerun`, or compare a named candidate
  run with `--candidate-run`.

## Installed Package And Source Checkouts

`qa-z summary` reads the same `.qa-z/runs/**` artifacts from an editable source
checkout, a wheel or sdist install, a virtual environment, or a pipx-like tool
environment. It needs local project access and `qa-z.yaml`; it does not depend
on a live PyPI package. The current public install path remains the GitHub
source or prerelease path documented by the repository.
