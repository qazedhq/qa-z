# Monthly Benchmark Report Template

## Month

`YYYY-MM`

## Summary

- Fixtures run: `<passed>/<total>` from `benchmarks/results/<run-id>/summary.json`
- Overall pass rate: `<overall_rate>` from the same summary artifact
- Regressions: `<count>` from `qa-z verify`
- New benchmark lanes: `<lane names>` or `None`
- Notable repair improvements: `<fixture ids>` with links to repair and verify artifacts

Do not include adoption, performance, or user-impact claims unless a linked release artifact, public issue, or user-provided source backs them.

## Agent Merge Safety Benchmark

| Lane | Baseline blockers | Candidate blockers | Verify verdict | Notes |
| --- | ---: | ---: | --- | --- |
| Codex | 2 | 0 | improved | Sample only; fixture `benchmarks/fixtures/improved_candidate/expected.json`; artifacts `.qa-z/runs/2026-05-codex/{baseline,candidate,verify}/`. |
| Claude Code | 1 | 1 | unchanged | Sample only; fixture `benchmarks/fixtures/unchanged_candidate/expected.json`; artifacts `.qa-z/runs/2026-05-claude-code/{baseline,candidate,verify}/`. |
| Cursor | 1 | 2 | regressed | Sample only; fixture `benchmarks/fixtures/regressed_candidate/expected.json`; artifacts `.qa-z/runs/2026-05-cursor/{baseline,candidate,verify}/`. |
| aider |  |  |  |  |
| OpenHands |  |  |  |  |
| Goose |  |  |  |  |

## Sample Monthly Report Checklist

Use this sample as structure, not as published results.

- Month: `2026-05`
- Validation: `python -m pytest -q tests/test_launch_growth_package.py`
- Validation artifact: `.qa-z/runs/2026-05-monthly-report/validation/pytest.txt`
- Fixture provenance: every row references a tracked `benchmarks/fixtures/*/expected.json` file.
- Evidence per row: fast summary, deep summary, repair prompt, candidate summary, verify report, and source fixture.
- Claims check: blocker counts and verdicts come from linked QA-Z artifacts; unsourced performance, adoption, and user claims are omitted.

## Evidence

Link to QA-Z run artifacts, SARIF, repair prompts, verification reports, and the fixture file behind each row.
