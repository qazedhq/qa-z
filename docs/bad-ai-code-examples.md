# Bad AI Code Examples

Common AI-generated merge risks:

## Auth bypass

- Pattern: removing a role or ownership check while keeping the happy path green.
- QA-Z signal: fast tests may pass, but deep rules or review evidence should point at the missing authorization branch.
- Repair expectation: restore the owner or role check, add a negative test, and verify that the fixed run improves without weakening the rule.

## Permission fallback

- Pattern: adding a fallback that silently grants access when a user, token, tenant, or policy lookup fails.
- QA-Z signal: the review packet should name the fallback path, affected files, and missing negative coverage.
- Repair expectation: fail closed, preserve explicit error handling, and add coverage for missing or malformed permission context.

## Test bypass

- Pattern: skipping, loosening, or deleting a failing test instead of fixing behavior.
- QA-Z signal: guard evidence should show changed tests, weaker assertions, or a mismatch between the failure and repair prompt.
- Repair expectation: restore the original assertion strength, fix the production behavior, and rerun guard or verify.

## Silent data migration risk

- Pattern: changing schema, defaults, or serialization without rollback, migration notes, or data tests.
- QA-Z signal: the QA contract should flag data/API risk and require deterministic validation before merge.
- Repair expectation: add migration or compatibility evidence, test old and new shapes, and document rollback or no-rollback reasoning.

## Broad refactor

- Pattern: touching unrelated modules to make a small AI-generated fix look tidy.
- QA-Z signal: review evidence should separate required files from unrelated churn and keep the repair prompt scoped.
- Repair expectation: shrink the diff to the behavior under review, then rerun the same gate.

## Dependency drift

- Pattern: adding or upgrading packages without explaining why existing tools are insufficient.
- QA-Z signal: package or lockfile changes should appear in review evidence and require a stated reason.
- Repair expectation: remove unnecessary dependencies or document the need, risk, and validation path.

## Generated code with no tests

- Pattern: adding large generated output with no deterministic gate.
- QA-Z signal: review evidence should identify generated or bulky files and missing validation.
- Repair expectation: add focused tests, fixture proof, or artifact-contract evidence before merge.
