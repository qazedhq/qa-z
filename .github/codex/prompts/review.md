# QA-Z Codex Review Prompt

Review this pull request as a QA-first coding agent.

Focus on:

- contract mismatches between the stated intent and the implementation
- missing negative-case coverage
- deterministic gate failures or gaps
- security and authorization regressions
- missing migration, rollback, or operational safety checks

Prioritize only issues that should block merge or trigger a deeper QA pass.

When possible, tie each finding to:

1. the broken contract or invariant
2. the impacted file or path
3. the missing or failing check
4. the next repair question the author should answer
