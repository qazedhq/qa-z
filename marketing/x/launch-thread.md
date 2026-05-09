# Launch Thread

Launch manually from the X UI. The thread should make the alpha status explicit
and point to checked-in assets:

- [docs/assets/qa-z-demo.svg](../../docs/assets/qa-z-demo.svg)
- [docs/assets/qa-z-demo.cast](../../docs/assets/qa-z-demo.cast)
- [docs/assets/qa-z-agent-auth-bug.cast](../../docs/assets/qa-z-agent-auth-bug.cast)

## Short Version

```text
Launch note: QA-Z 🛡️ v0.9.9-alpha is available as a GitHub prerelease.

It is alpha tooling for deterministic QA evidence around agent-generated code.

Repo: https://github.com/qazedhq/qa-z
Release: https://github.com/qazedhq/qa-z/releases/tag/v0.9.9-alpha
```

## Long Thread

```text
1/ QA-Z 🛡️ v0.9.9-alpha is live as a GitHub prerelease.

Goal: make AI coding safe to merge with deterministic QA evidence, not vague advice.

Repo: https://github.com/qazedhq/qa-z

2/ Coding agents are fast. The merge decision still needs contracts, checks, repairable feedback, and verification a human can inspect.

QA-Z is built around that control plane.

3/ The current alpha covers QA contracts, fast checks, Semgrep-backed deep checks, review packets, repair prompts, and post-repair verification.

No package-registry publish is claimed.

4/ Demo assets are checked in:

docs/assets/qa-z-demo.svg
docs/assets/qa-z-demo.cast
docs/assets/qa-z-agent-auth-bug.cast

They show QA-Z catching a risky agent auth change before merge.

5/ This is alpha software. The useful thing to test is the workflow:

Can QA-Z turn an agent change into clear pass/fail evidence and a repair prompt?

Release: https://github.com/qazedhq/qa-z/releases/tag/v0.9.9-alpha

6/ Feedback wanted:

What deterministic checks would you require before merging AI-generated code in your repo?

Issues and discussion belong here: https://github.com/qazedhq/qa-z
```

## What Not To Claim

- Do not claim PyPI, TestPyPI, package-registry, or GitHub Marketplace
  availability.
- Do not claim adoption numbers, customers, testimonials, or production use.
- Do not imply QA-Z replaces human review.
- Do not imply QA-Z posts, follows, or replies on X automatically.
