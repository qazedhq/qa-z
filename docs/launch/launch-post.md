# Launch Post Drafts

These drafts are starting points for public launch surfaces. They intentionally
avoid adoption numbers, package-registry claims, or claims that QA-Z edits code.

## GitHub Release / Repository Post

QA-Z is the safety belt for AI-generated code.

Coding agents write code quickly. QA-Z turns their changes into deterministic
merge evidence: QA contracts, fast checks, Semgrep-backed deep checks, repair
prompts, and post-repair verification.

Try the local auth-bug demo, inspect the generated `.qa-z` artifacts, and open a
good-first issue from the launch queue if you want to help make agent-generated
code safer to merge.

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

Alpha prerelease: https://github.com/qazedhq/qa-z/releases/tag/v0.9.9-alpha
Repo: https://github.com/qazedhq/qa-z
