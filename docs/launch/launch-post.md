# Launch Post Drafts

These drafts are starting points for public launch surfaces. They intentionally
avoid adoption numbers, package-registry claims, or claims that QA-Z edits code.

## GitHub Repository Post

QA-Z makes AI coding safe to merge.

Coding agents write code quickly. QA-Z turns their changes into deterministic
merge evidence: QA contracts, fast checks, Semgrep-backed deep checks, repair
prompts, and post-repair verification.

Try the terminal demo in the README, inspect the checked-in casts under
`docs/assets/`, and run the local auth-bug example to see QA-Z stop a risky auth
change before merge.

## Hacker News

Show HN: QA-Z - deterministic QA gates for AI-generated code

I built QA-Z as a small, model-agnostic QA control plane for coding agents. It
does not call live agents or make merge decisions with an LLM. It creates the
contracts, checks, review packets, repair prompts, SARIF, GitHub summaries, and
verification reports that help a human decide whether AI-generated code is safe
to merge.

The current alpha is a GitHub prerelease only. No package registry publish has happened yet.

## X / LinkedIn

Coding agents write code.

QA-Z tells you if that code is safe to merge.

It wraps agent-generated changes in deterministic QA evidence: contracts,
checks, repair prompts, and post-repair verification.

Terminal demo: https://github.com/qazedhq/qa-z/blob/main/docs/assets/qa-z-demo.cast
Alpha prerelease: https://github.com/qazedhq/qa-z/releases/tag/v0.9.9-alpha
Repo: https://github.com/qazedhq/qa-z
