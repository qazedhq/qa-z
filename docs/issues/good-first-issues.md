# Good First Issue Seeds

Open these as GitHub issues when issue-write access is available. Each seed names files, acceptance, and validation so contributors can land deterministic improvements.

## Issue 1: Record the agent-auth-bug asciinema

Files: `docs/assets/qa-z-agent-auth-bug.cast`, `docs/demo-script.md`

Acceptance: the recording shows `qa-z plan`, `qa-z fast`, `qa-z deep`, `qa-z repair-prompt`, and `qa-z verify`.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`

## Issue 2: Add a GIF generated from the asciinema

Files: `docs/assets/`, `README.md`

Acceptance: README links to a short visual demo without replacing the text commands.

Validation: `python -m pytest -q tests/test_public_docs_current_truth.py`

## Issue 3: Improve the FastAPI agent bug walkthrough

Files: `examples/fastapi-agent-bug/`, `docs/walkthroughs/auth-bug.md`

Acceptance: FastAPI auth check failure remains reproducible and the fixed implementation verifies improved.

Validation: `qa-z fast --path examples/fastapi-agent-bug --output-dir .qa-z/runs/qa-z-fastapi-agent-bug`

## Issue 4: Add a second Semgrep rule to the auth demos

Files: `examples/agent-auth-bug/semgrep-rules/`, `examples/fastapi-agent-bug/semgrep-rules/`

Acceptance: Semgrep reports deterministic auth evidence without noisy network or live-agent dependencies.

Validation: `qa-z deep --path examples/agent-auth-bug --output-dir .qa-z/runs/qa-z-auth-deep`

## Issue 5: Add a TypeScript agent bug walkthrough

Files: `examples/typescript-agent-bug/`, `docs/walkthroughs/`

Acceptance: TypeScript agent bug demo documents baseline failure, candidate fix, and QA-Z verification.

Validation: `qa-z fast --path examples/typescript-agent-bug --output-dir .qa-z/runs/qa-z-ts-agent-bug`

## Issue 6: Add a monorepo quickstart

Files: `docs/quickstart.md`, `docs/public-roadmap.md`

Acceptance: mixed Python/TypeScript repositories have a clear install and gate path.

Validation: `python -m pytest -q tests/test_public_docs_current_truth.py`

## Issue 7: Add GitHub Actions summary screenshot

Files: `docs/github-action.md`, `docs/assets/`

Acceptance: screenshot or terminal capture shows the QA-Z job summary and artifact pointers.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`

## Issue 8: Add SARIF code scanning screenshot

Files: `docs/walkthroughs/sarif-code-scanning.md`, `docs/assets/`

Acceptance: docs show where `deep/results.sarif` appears in GitHub code scanning.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`

## Issue 9: Expand comparison with aider, OpenHands, and Goose

Files: `docs/comparison.md`, `README.md`

Acceptance: QA-Z is framed as a QA layer around these tools, not a competitor.

Validation: `python -m pytest -q tests/test_public_docs_current_truth.py`

## Issue 10: Wire OpenSSF Scorecard badge docs

Files: `.github/workflows/scorecard.yml`, `docs/scorecard.md`

Acceptance: OpenSSF Scorecard trust surface is documented and the workflow remains least-privilege.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`

## Issue 11: Add public roadmap issue template

Files: `.github/ISSUE_TEMPLATE/`, `docs/public-roadmap.md`

Acceptance: roadmap proposals ask for evidence, validation, and user impact.

Validation: `python -m pytest -q tests/test_public_docs_current_truth.py`

## Issue 12: Add copy-this-prompt-to-Codex snippet card

Files: `docs/use-with-codex.md`, `README.md`

Acceptance: docs include a compact prompt that points Codex at `.qa-z/runs/latest/repair/codex.md`.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`

## Issue 13: Add Use with Semgrep examples for custom rules

Files: `docs/use-with-semgrep.md`, `examples/*/semgrep-rules/`

Acceptance: docs show local custom rule config and SARIF output.

Validation: `qa-z deep --path examples/fastapi-agent-bug --output-dir .qa-z/runs/qa-z-fastapi-agent-deep`

## Issue 14: Add TestPyPI publish rehearsal checklist

Files: `docs/package-publish-plan.md`, `docs/releases/`

Acceptance: publish rehearsal includes build, artifact smoke, pipx, and uv commands.

Validation: `python scripts/alpha_release_artifact_smoke.py --json`

## Issue 15: Add monthly benchmark report sample

Files: `docs/monthly-benchmark-report-template.md`, `docs/agent-merge-safety-benchmark.md`

Acceptance: sample report ties benchmark rows to QA-Z run artifacts.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`

## Issue 16: Add hosted demo static page plan

Files: `docs/hosted-demo.md`, `docs/docs-site.md`

Acceptance: hosted demo remains replayable locally and does not imply QA-Z Cloud.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`

## Issue 17: Add community examples guide

Files: `docs/community-distribution.md`, `docs/public-roadmap.md`

Acceptance: contributors know what evidence a community example must include.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`

## Issue 18: Add optional PR comment dry-run screenshot

Files: `templates/.github/workflows/qa-z-pr-comment.yml`, `docs/pr-summary-comment.md`

Acceptance: opt-in comment behavior is documented with `QA_Z_POST_PR_COMMENT=false` by default.

Validation: `python -m pytest -q tests/test_launch_growth_package.py tests/test_github_workflow.py`

## Issue 19: Add enterprise case study template

Files: `docs/case-studies.md`

Acceptance: template asks for before/after evidence, commands, and non-goals.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`

## Issue 20: Add OpenSSF Scorecard follow-up issue

Files: `docs/scorecard.md`, `.github/workflows/scorecard.yml`

Acceptance: issue explains how to inspect the first Scorecard run and convert findings into deterministic tasks.

Validation: `python -m pytest -q tests/test_launch_growth_package.py`
