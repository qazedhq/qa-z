# Day 3 - Security Angle

## Goal

Connect QA-Z to AppSec and secure code review without overstating automation.

## Post

```text
Security angle for AI coding:

When an agent changes auth or input handling, reviewers need evidence they can rerun.

QA-Z adds contracts, checks, and repair prompts around that merge decision.

Repo: https://github.com/qazedhq/qa-z
```

## Optional Thread

```text
1/ QA-Z can use Semgrep-backed deep checks as part of the evidence packet, but deterministic gates stay visible.

2/ The alpha goal is not "LLM says safe." It is "the repo produced concrete evidence for a human merge decision."
```

## Link Targets

- Repository: [https://github.com/qazedhq/qa-z](https://github.com/qazedhq/qa-z)
- Semgrep docs:
  [https://github.com/qazedhq/qa-z/blob/main/docs/use-with-semgrep.md](https://github.com/qazedhq/qa-z/blob/main/docs/use-with-semgrep.md)

## What Not To Claim

- Do not claim complete security coverage.
- Do not claim package-registry publishing.
- Do not claim QA-Z certifies code as secure.
