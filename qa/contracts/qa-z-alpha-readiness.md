---
qa_z_contract_version: 1
title: "QA Contract: QA-Z Alpha Readiness"
---

# QA Contract: QA-Z Alpha Readiness

## Scope

Keep the QA-Z alpha control plane executable for local repository validation.

## Assumptions

- The repository is validated from the checked-out working tree.
- Local QA flows must not depend on live model execution.
- Remote publication may remain externally blocked by repository visibility.

## Invariants

- `qa-z fast` and `qa-z deep` use deterministic subprocess checks.
- Configured adapter files are explicit onboarding artifacts.
- Release evidence must distinguish local code failures from external publish blockers.

## Risk Edges

- README-only contract directories must not be treated as valid generated contracts.
- Smart selection must preserve configured commands while narrowing targets.
- Semgrep targeted scans must replace broad positional roots with selected targets.

## Negative Cases

- Missing agent instruction files should be reported by `qa-z doctor`.
- Legacy `checks.deep` config should remain visible as a warning path.
- Missing GitHub repositories should stay classified as external bootstrap blockers.

## Acceptance Checks

- `python -m pytest`
- `python -m ruff check src tests scripts`
- `python -m ruff format --check src tests scripts`
- `python -m mypy src tests`
