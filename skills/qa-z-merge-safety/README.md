# QA-Z Merge Safety

This skill gives coding agents a compact QA loop:

```text
contract -> fast -> deep -> review -> repair prompt -> verify -> merge verdict
```

Use it when AI-generated code needs deterministic merge evidence instead of a confidence statement.

## Scope

- Require an explicit QA contract before review.
- Run deterministic fast checks before slower analysis.
- Preserve deep-check artifacts for reviewer evidence.
- Turn failed evidence into a repair prompt.
- Verify the repaired candidate before merge.

## Boundaries

- Do not replace deterministic gates with LLM-only judgment.
- Do not create commits, pushes, releases, or package publishes.
- Do not hide skipped checks behind a passing summary.
- Do not move Codex or Claude behavior into the core QA-Z engine.

## Expected Output

The agent should finish with the commands it ran, the verdict, and the artifact paths a reviewer can inspect.
