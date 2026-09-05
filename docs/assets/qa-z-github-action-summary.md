# QA-Z GitHub Action Summary Example

This is a deterministic local auth-bug example, not a live GitHub run.
The guard action appends this shape to `$GITHUB_STEP_SUMMARY` when
`qa-z guard --github-summary` writes `.qa-z/runs/latest/guard/github-summary.md`.

# QA-Z Summary

**Fast:** failed
**Deep:** not run
**Selection:** smart
**Contract:** `qa/contracts/ai-auth-bug.md`

## Fast QA

- Passed: 0
- Failed: 1
- Skipped: 0
- Warning: 0

## Failed Checks

- `auth_policy` - full - full run required because no changed files were found

## Changed Files

- No changed-file metadata was captured.

## Selection

- Input source: none
- Full: `auth_policy`
- Targeted: none
- Skipped: none

## Next

- Fast summary: `.qa-z/runs/latest/fast/summary.json`
- Review packet: `.qa-z/runs/latest/review/review.md`
- Repair prompt: `.qa-z/runs/latest/repair/prompt.md`
