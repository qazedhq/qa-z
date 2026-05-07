# Bad AI Code Examples

Common AI-generated merge risks:

- Auth bypass: removing a role or ownership check while keeping the happy path green.
- Silent data migration risk: changing schema or defaults without rollback and data tests.
- Broad refactor: touching unrelated modules to make a small fix look tidy.
- Flaky test masking: skipping or loosening a failing test instead of fixing behavior.
- Dependency drift: adding or upgrading packages without documenting why.
- Generated code with no tests: adding large output with no deterministic gate.
