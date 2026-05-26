# Next Real Product Slices

Use this file after the operating model is in place. It is a candidate queue,
not proof that the behavior is currently broken or fixed. Verify repo state
before editing.

## Selection Rule

- QA-Z improvements must improve QA judgment, evidence, benchmark coverage,
  repair prompt quality, or current-truth routing.
- Do not mutate target repositories, push branches, deploy, or add hidden
  network/model behavior.
- Prefer deterministic tests and fixtures over narrative roadmap edits.

## Slice 1 - Stale roadmap/select-next regression guard

- Priority: P0/P1
- Flow: current truth -> self-inspect/select-next -> recommended QA slice.
- User-visible outcome: QA-Z stops recommending already-stale or
  already-completed tasks.
- Discovery commands:
  - `rg -n "self-inspect|select-next|roadmap|current-state|current truth|stale" src tests docs benchmarks pyproject.toml`
- Likely change type: Contract Slice + Evidence Slice.
- Validation candidates: targeted pytest around select-next/self-inspect; then
  `python -m pytest -q` if blast radius warrants.
- Stop rule: Do not commit generated runtime evidence as source truth.

## Slice 2 - GitHub Actions repair/verify summary UX

- Priority: P1
- Flow: guard -> repair prompt -> verify -> GitHub Actions Job Summary/artifacts.
- User-visible outcome: CI users see the same repair/verify next command and
  artifact pointers that local users get from `qa-z verify --from-run`.
- Discovery commands:
  - `rg -n "github-summary|GITHUB_STEP_SUMMARY|verify|repair-prompt|next_actions|artifacts" src tests docs .github`
- Likely change type: Flow Slice + Evidence Slice.
- Validation candidates: targeted GitHub summary/render tests plus verify
  workflow tests.
- Stop rule: Keep PR comments, SARIF upload, branch mutation, release, and
  deploy behavior opt-in or out of scope.

## Slice 3 - Benchmark fixture coverage and lock behavior

- Priority: P1
- Flow: benchmark fixture -> result policy -> report/summary -> guard decision.
- User-visible outcome: Benchmark output is deterministic and parallel
  experiments do not corrupt default result directories.
- Discovery commands:
  - `rg -n "benchmark|results-dir|lock|fixture|summary.json|report.md" src tests benchmarks docs`
- Likely change type: Evidence Slice.
- Validation candidates: targeted benchmark fixture test;
  `python -m qa_z benchmark --json` when safe.
- Stop rule: Use separate results dirs for parallel or scratch experiments.
