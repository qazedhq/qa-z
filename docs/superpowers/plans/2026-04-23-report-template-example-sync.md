# Report Template Example Sync Plan

**Goal:** Close the remaining Priority 4 continuity drift by aligning README,
workflow/template non-goals, and roadmap immediate-focus guidance with the
actual shipped template/example surfaces.

**Context / repo evidence:**

- `docs/reports/current-state-analysis.md` already recommends report/template/example
  sync as the next focus after L26.
- `docs/reports/next-improvement-roadmap.md` still carries broader legacy
  ordering language, so the immediate next package is not stated clearly in the
  roadmap itself.
- `README.md` currently describes `examples/` as runnable Python and TypeScript
  demos even though `examples/nextjs-demo/README.md` makes clear that one
  shipped example directory is placeholder-only.
- `.github/workflows/ci.yml` and `templates/.github/workflows/vibeqa.yml`
  already avoid live executor behavior, but their file-level comments do not
  explicitly encode all of the non-goals that README now documents, especially
  `executor-result` ingest and autonomous repair.

**Decision:**

- Keep the package narrow and documentation-oriented: no runtime behavior or CLI
  contract changes.
- Add current-truth tests first so README/workflow/roadmap wording becomes a
  locked public contract instead of a best-effort narrative.
- Sync README repository-map language so examples are described honestly as a
  mix of runnable demos and placeholder surfaces.
- Sync workflow and template file comments with the live-free non-goals already
  documented in README.
- Add an explicit post-package handoff so the roadmap says Priority 5 executor
  operator diagnostics is next once the Priority 4 sync pass closes.

**Scope:**

- README repository-map wording for `examples/`
- README near-term roadmap ordering
- workflow/template top-level non-goal comments
- roadmap immediate-focus continuity line
- current-truth/workflow tests that pin those surfaces

## Verification Plan

- `python -m pytest -q tests/test_current_truth.py tests/test_examples.py tests/test_github_workflow.py tests/test_cli.py`
- `python -m pytest`
- `python -m qa_z benchmark --json --results-dir %TEMP%\qa-z-l27-full-benchmark`
- `python -m mypy src tests`
- `python -m ruff check .`
- `python -m ruff format --check .`

## Blocker

- type: `AMBIGUITY`
- location: `README.md`, `docs/reports/current-state-analysis.md`, `docs/reports/next-improvement-roadmap.md`
- symptom: public and continuity docs still treated report/template/example sync plus standalone GitHub annotation helpers as the next roadmap package even after the sync pass had landed and extra annotation surfaces remained deferred
- root cause (hypothesis): the repo had an in-package "Priority 4 is next" handoff, but no post-package closure pass yet to move every doc surface to the new next focus
- unblock condition: README, current-state, roadmap, and current-truth tests all agree that Priority 5 executor operator diagnostics is the next package and that report/template/example sync is now maintenance
- risk: a new session could reopen already-landed sync work or promote a deferred GitHub annotation surface ahead of the actual operator-diagnostics gap

## Resolution Plan

- refresh README near-term roadmap ordering so it no longer advertises deferred GitHub annotation work as near-term
- move current-state and roadmap continuity docs from "Priority 4 is next" to the post-sync Priority 5 handoff
- lock the new handoff, README roadmap wording, and workflow-template non-goals in `tests/test_current_truth.py`
- rerun focused regression, then rerun full pytest plus benchmark/static checks to refresh the continuity evidence

## Result

- resolved
- evidence: README near-term roadmap now starts with operator-diagnostics depth, current-state reordered its next priorities around the post-sync gap, the roadmap now marks Priority 4 as a closed first pass and names Priority 5 as the immediate next focus, and the plan/worklog surfaces now record the same handoff
- remaining risk: report/template/example sync is still a maintenance lane, so future public-doc edits can drift again if current-truth coverage is not kept alongside them

## Outcome

- README now keeps its public repo map, public example wording, and near-term roadmap aligned with the actual shipped alpha surface
- current-state and roadmap docs now explicitly say the workflow and workflow template do not call live executors, ingest executor results, or perform autonomous repair
- the continuity handoff now names Priority 5 executor operator diagnostics as the next package instead of leaving Priority 4 open after it landed

## Verification Results

- `python -m pytest -q tests/test_current_truth.py tests/test_examples.py tests/test_github_workflow.py tests/test_cli.py` -> `90 passed`
- `python -m pytest` -> `1139 passed`
- `python -m qa_z benchmark --json --results-dir %TEMP%\qa-z-l27-full-benchmark` -> `53/53 fixtures, overall_rate 1.0`
- `python -m mypy src tests` -> `Success: no issues found in 494 source files`
- `python -m ruff check .` -> `passed`
- `python -m ruff format --check .` -> `704 files already formatted`

## Next Focus

- Shift the immediate roadmap focus to Priority 5 executor operator diagnostics; keep report/template/example sync as a maintenance lane rather than a fresh feature line.
