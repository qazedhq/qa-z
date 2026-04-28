# Executor Operator Publish Action Lines Plan

**Goal:** Deepen Priority 5 operator-facing diagnostics by making repair-session
outcome Markdown and GitHub-summary publish Markdown preserve ordered dry-run
action ids plus summaries instead of flattening mixed-history action residue
into one sentence.

**Context / repo evidence:**

- `docs/reports/current-state-analysis.md` and
  `docs/reports/next-improvement-roadmap.md` both name Priority 5 executor
  operator diagnostics as the immediate next package.
- `src/qa_z/executor_dry_run_render.py` already renders ordered dry-run action
  lines as ``- `action_id`: summary`` in `dry_run_report.md`, so a higher-fidelity
  operator-facing format already exists locally.
- `src/qa_z/repair_session_outcome.py` and
  `src/qa_z/reporters/verification_publish.py` currently collapse
  `executor_dry_run_recommended_actions` into one `Dry-run recommended actions:`
  line via summary-only helpers.
- `tests/test_verification_publish_session.py` currently pins history-fallback
  publish residue for repeated partial and scope-validation cases, but not the
  richer blocked mixed-history contract already committed in
  `benchmarks/fixtures/executor_dry_run_blocked_mixed_history_operator_actions/expected.json`.
- `README.md` already claims GitHub-facing summaries preserve operator decision,
  operator summary, and recommended action residue, so preserving the ordered
  action ids in those Markdown surfaces is a natural depth step rather than a
  new product area.

**Decision:**

- Keep dry-run verdict logic, action ordering, and benchmark fixtures unchanged.
- Add failing tests first for session outcome Markdown and publish-summary
  Markdown that expect ordered `Action <id>:` lines for mixed-history and
  single-action fallback cases.
- Implement one shared rendering helper for operator-facing action lines so
  repair-session outcomes and publish summaries stay aligned.
- Extend current-truth and continuity docs to say operator-facing Markdown now
  preserves ordered action ids alongside action summaries.

**Scope:**

- `src/qa_z/repair_session_outcome.py`
- `src/qa_z/reporters/verification_publish.py`
- `tests/test_repair_session.py`
- `tests/test_verification_publish_session.py`
- `tests/test_current_truth.py`
- `README.md`
- `docs/reports/current-state-analysis.md`
- `docs/reports/next-improvement-roadmap.md`

## Verification Plan

- `python -m pytest -q tests/test_repair_session.py tests/test_verification_publish_session.py tests/test_current_truth.py`
- `python -m pytest`
- `python -m qa_z benchmark --json --results-dir %TEMP%\qa-z-l28-full-benchmark`
- `python -m mypy src tests`
- `python -m ruff check src/qa_z/repair_session_outcome.py src/qa_z/reporters/verification_publish.py tests/test_repair_session.py tests/test_verification_publish_session.py tests/test_current_truth.py`
- `python -m ruff format --check .`

## Blocker

- type: `AMBIGUITY`
- location: `src/qa_z/repair_session_outcome.py`, `src/qa_z/reporters/verification_publish.py`
- symptom: operator-facing Markdown surfaces claim to preserve recommended
  action residue, but they currently flatten ordered actions into summary-only
  text and hide the stable action ids that dry-run reports already expose
- root cause (hypothesis): earlier Priority 5 work focused on deterministic
  verdict/action selection and did not yet extend the `Action <id>:` rendering
  contract to outcome/publish Markdown surfaces
- unblock condition: outcome Markdown and publish-summary Markdown both render
  ordered action lines with stable ids while keeping existing verdict/summary
  residue intact
- risk: operators reading outcome or GitHub-summary surfaces lose the direct
  action id needed to map residue back to deterministic retry guidance

## Resolution Plan

- add failing tests that demand ordered action lines in repair-session outcome
  and history-fallback publish-summary Markdown
- implement a shared action-line renderer and replace the old flat
  `Dry-run recommended actions:` line on those two surfaces
- sync README and continuity docs so the public/current-truth contract names the
  stronger operator-facing Markdown behavior
- rerun focused regression, then full pytest/benchmark/static checks

## Result

- resolved
- evidence: repair-session outcome Markdown and GitHub-facing publish summaries
  now render `- Action \`<id>\`: ...` lines for dry-run recommended actions,
  `tests/test_verification_publish_session.py` now pins a blocked mixed-history
  history-fallback case with ordered action residue, and README/current-state/
  roadmap/current-truth now record the stronger publish-surface contract
- remaining risk: Priority 5 still lacks one more non-blocked mixed-history
  depth slice that combines validation conflict with repeated rejected-result
  retry pressure

## Outcome

- landed a shared `src/qa_z/operator_action_render.py` helper so outcome and
  publish surfaces reuse the same ordered action-line renderer
- kept dry-run verdict logic and benchmark fixtures unchanged while improving
  operator-facing Markdown fidelity
- shrank the publish-session regression file back under its architecture budget
  by moving repeated attempt construction into `tests/verification_publish_test_support.py`

## Verification Results

- `python -m pytest -q tests/test_repair_session.py tests/test_verification_publish_session.py tests/test_current_truth.py tests/test_executor_dry_run_render.py tests/test_executor_history_dry_run_layout_architecture.py tests/test_verification_publish_architecture.py` -> `62 passed`
- `python -m pytest` -> `1140 passed`
- `python -m qa_z benchmark --json --results-dir %TEMP%\\qa-z-l28-final-benchmark` -> `53/53 fixtures, overall_rate 1.0`
- `python -m mypy src tests` -> `Success: no issues found in 495 source files`
- `python -m ruff check .` -> `passed`
- `python -m ruff format --check .` -> `705 files already formatted`

## Next Focus

- Stay in Priority 5 and add a non-blocked mixed-history operator-diagnostics
  slice that combines validation conflict and repeated rejected-result retry
  pressure across logic, benchmark, publish, and current-truth surfaces.
