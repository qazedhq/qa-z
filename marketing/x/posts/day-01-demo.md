# Day 1 - Demo / Auth Bug

## Goal

Point people to the checked-in auth-bug demo assets and show QA-Z as
evidence-first merge safety.

## Post

```text
Demo angle for QA-Z:

An agent writes a risky auth change. QA-Z turns it into pass/fail evidence and a repair prompt before merge.

Cast: https://github.com/qazedhq/qa-z/blob/main/docs/assets/qa-z-agent-auth-bug.cast
Repo: https://github.com/qazedhq/qa-z
```

## Optional Thread

```text
1/ The demo is intentionally small: auth behavior, deterministic checks, Semgrep signal, and a repair loop a reviewer can inspect.

2/ The point is not that QA-Z is magic. The point is that merge safety should produce repairable evidence instead of vague unease.
```

## Link Targets

- Auth-bug cast:
  [https://github.com/qazedhq/qa-z/blob/main/docs/assets/qa-z-agent-auth-bug.cast](https://github.com/qazedhq/qa-z/blob/main/docs/assets/qa-z-agent-auth-bug.cast)
- Repository: [https://github.com/qazedhq/qa-z](https://github.com/qazedhq/qa-z)

## What Not To Claim

- Do not claim the demo proves production readiness.
- Do not claim package-registry publishing.
- Do not claim QA-Z replaces human review.
