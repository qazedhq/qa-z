# QA-Z demo output

This transcript was captured from a temporary copy of `examples/fastapi-demo/` on April 29, 2026. It uses only local commands and does not call Codex, Claude, or any external model API.

Commands:

```bash
python -m qa_z plan --path <demo-copy> --title "Protect invoice access" --issue issue.md --spec spec.md --slug protect-invoice-access --overwrite
python -m qa_z fast --path <demo-copy> --output-dir <demo-copy>/.qa-z/runs/preview-fast
python -m qa_z review --path <demo-copy> --from-run <demo-copy>/.qa-z/runs/preview-fast
python -m qa_z repair-prompt --path <demo-copy> --from-run <demo-copy>/.qa-z/runs/preview-fast --adapter codex
```

Output:

```text
created contract: qa/contracts/protect-invoice-access.md
qa-z fast: passed
Contract: qa/contracts/protect-invoice-access.md
Summary: .qa-z/runs/preview-fast/fast/summary.json
# QA-Z Review Packet

- Contract: qa/contracts/protect-invoice-access.md
- Mode: qa-z review

## Reviewer Focus

- Billing and checkout flows should preserve access controls and money movement safety.

## Negative Cases To Check

- Reject invalid or incomplete input for the changed behavior.
- Preserve existing behavior for unchanged happy-path flows.

## Required Evidence

- Run fast checks: py_lint, py_format, py_test.
- Review the change against this contract before merge.
- Escalate to deeper checks if critical paths or security-sensitive code changed.

## Suggested Fast Checks

- py_lint
- py_format
- py_test

## Suggested Deep Checks

- No deep checks configured.

## Run Verdict

- Status: passed
- Run directory: `.qa-z/runs/preview-fast`
- Summary: `.qa-z/runs/preview-fast/fast/summary.json`

## Check Selection

- Mode: full
- Input source: none
- Changed files: 0
- Full checks: py_lint, py_format, py_test
- Targeted checks: none
- Skipped checks: none
- High-risk reasons: none

## Executed Checks

- py_lint: passed (lint, ruff, exit 0)
- py_format: passed (format, ruff, exit 0)
- py_test: passed (test, python, exit 0)

## Failed Checks

No failed checks were found.

## Review Priority Order

No failed checks require priority ordering.
# QA-Z Codex Repair Handoff

Implement the repair now.
Use only the QA-Z evidence in this packet. Keep the diff focused.

## Run

- Status: passed
- Run: `.qa-z/runs/preview-fast`
- Fast summary: `.qa-z/runs/preview-fast/fast/summary.json`
- Contract: `qa/contracts/protect-invoice-access.md`

## Repair Targets

No blocking repair targets were selected.

## Affected Files

- none

## Constraints

- Do not weaken tests.
- Do not remove lint/type checks to make the run pass.
- Preserve existing CLI flags and artifact names unless the contract explicitly changes them.

## Non-Goals

- Do not call Codex, Claude, or any external LLM/API from QA-Z.
- Do not build a scheduler, queue, or remote execution controller.
- Do not make unrelated refactors or broad architecture changes.

## Validation Commands

- `python -m qa_z fast` - qa-z fast exits with code 0.

## Success Criteria

- No repair required; source run already passed
- No unrelated changes were introduced.
```
