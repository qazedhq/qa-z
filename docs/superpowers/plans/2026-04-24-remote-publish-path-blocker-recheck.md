# QA-Z Remote Publish Path Blocker Recheck

Date: 2026-04-24
Branch context: `codex/qa-z-bootstrap`

## Objective

Recheck the live remote publish blocker after the local alpha release gate
stabilized, and record whether Stage 4-5 can advance or remain blocked.

## Scope

1. Re-read the compact release/state docs before acting.
2. Re-verify configured `origin` and direct remote preflight against the
   intended GitHub target.
3. Re-check visible GitHub account and org scope from this session.
4. Update durable docs so the next session can resume from repository evidence
   instead of chat memory.

## Repository Evidence

- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`
- `docs/releases/v0.9.8-alpha-publish-handoff.md`
- `docs/superpowers/plans/2026-04-23-release-readiness-stages-1-5-execution.md`
- `git remote -v`
- `python scripts/alpha_release_preflight.py --repository-url https://github.com/qazedhq/qa-z.git --expected-origin-url https://github.com/qazedhq/qa-z.git --allow-dirty --json --output .qa-z/tmp/alpha-release-preflight-remote-live.json`
- GitHub app search for `qazedhq qa-z`
- GitHub app installed-account and org visibility

## Design Decision

- Keep the current repo-local release truth untouched unless fresh evidence
  disproves it.
- Treat remote publish as blocked until both repository existence and session
  visibility are confirmed.
- If the blocker remains external, document it explicitly instead of inventing a
  repo-local Stage 4-5 task.

## BLOCKER

- type: EXTERNAL + ACCESS
- location: direct remote preflight and GitHub owner visibility for
  `https://github.com/qazedhq/qa-z.git`
- symptom: direct remote preflight still fails on `github_repository` and
  `remote_reachable`, GitHub repository search returns no visible `qazedhq/qa-z`
  result, and the only installed account visible to this session is
  `ggbu75769-dot` with no visible org membership
- root cause (hypothesis): the intended public repository still does not exist
  or is not visible from this session, and the session is not installed on the
  target owner
- unblock condition: create or expose `qazedhq/qa-z`, or install/authorize this
  session on that owner, then rerun remote preflight against the configured
  `origin`
- risk: publish, release PR, branch push, and tag cutover cannot be verified
  honestly while the target owner remains unreachable

## RESOLUTION PLAN

- steps:
  - recheck `origin`
  - rerun direct remote preflight
  - recheck installed GitHub accounts and org visibility
  - sync state/worklog/release handoff docs with the live blocker evidence
- verification:
  - remote preflight JSON reflects the current blocker
  - targeted current-truth regression pins the handoff wording

## RESULT

- unresolved external blocker
- evidence:
  - `git remote -v` still points to `https://github.com/qazedhq/qa-z.git`
  - direct remote preflight still failed with
    `release_path_state=blocked_repository`,
    `remote_readiness=needs_repository_bootstrap`, and
    `remote_blocker=repository_missing`
  - `git ls-remote --refs https://github.com/qazedhq/qa-z.git` still returned
    `remote: Repository not found.`
  - GitHub app search returned no visible `qazedhq/qa-z` repository
  - installed GitHub accounts still show only `ggbu75769-dot`
  - visible GitHub org membership is empty
  - a first local `alpha_release_gate` rerun failed only on `ruff_format`
    because the touched current-truth test files were not yet reformatted
  - after `python -m ruff format tests/test_current_truth.py tests/test_current_truth_release_handoff.py tests/test_current_truth_release_surfaces.py`, `python -m pytest` passed with `1158 passed`
  - `python scripts/alpha_release_gate.py --allow-dirty --json --output .qa-z/tmp/alpha-release-gate-l36.json` then passed locally with `1158 passed`, `54/54 fixtures, overall_rate 1.0`, build/artifact smoke/bundle manifest green, and nested local preflight `remote_readiness=ready_for_remote_checks`
- remaining risk:
  - Stage 4-5 remain blocked until the target repository exists and this session
    can see it

## Follow-Up

- Create or expose `qazedhq/qa-z`, or install/authorize access to that owner
  for this session.
- Rerun direct remote preflight.
- Only after remote preflight turns green should the release flow choose direct
  publish versus release-PR cutover.
