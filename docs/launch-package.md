# QA-Z Launch Package

This package turns the repository from an internal engineering surface into a public launch surface.

## Positioning

Primary line:

```text
QA-Z is the safety belt for AI-generated code.
```

Supporting lines:

```text
Coding agents write code. QA-Z tells you if that code is safe to merge.
Stop trusting AI code blindly. Run QA-Z before you merge it.
```

Category:

```text
AI Code QA
```

## Repository Topics

Recommended topics:

```text
ai
ai-agents
coding-agents
developer-tools
qa
testing
ci
code-review
devsecops
semgrep
sarif
codex
claude
cursor
github-actions
static-analysis
python
typescript
agentic-ai
quality-assurance
```

## Social Preview

Use [assets/qa-z-social-preview.png](assets/qa-z-social-preview.png) as the GitHub social preview upload. The editable SVG source is [assets/qa-z-social-preview.svg](assets/qa-z-social-preview.svg). Both are sized at `1280 x 640`.

Text:

```text
QA-Z
The safety belt for AI-generated code.
Contracts. Checks. Repair prompts. Verification.
github.com/qazedhq/qa-z
```

## Good First Issue Seeds

Open issues from this list as the public launch queue:

See [docs/issues/good-first-issues.md](issues/good-first-issues.md) for 20 detailed good-first-issue seeds with files, acceptance, and validation.

1. Add a screenshot or asciinema capture for the agent-auth-bug demo.
2. Add a Python package quickstart that uses `pipx` from a GitHub tag.
3. Add a `uv tool install` smoke note after TestPyPI or PyPI publish.
4. Add a second Semgrep rule to the auth-bug demo.
5. Add a TypeScript auth-bug demo with Vitest.
6. Add a monorepo quickstart for mixed Python and TypeScript repositories.
7. Add a GitHub Actions summary screenshot to the docs.
8. Add a SARIF/code-scanning walkthrough.
9. Add a comparison page section for aider, OpenHands, and Goose.
10. Add an OpenSSF Scorecard setup note.
11. Add a public roadmap issue template.
12. Add a docs page for reading `.qa-z/runs/latest/repair/codex.md`.

## Release Checklist

- GitHub prerelease exists for `v0.9.8-alpha`.
- README first screen uses the safety-belt positioning.
- The five-minute auth-bug demo is runnable locally.
- Quickstart, comparison, GitHub Action, Codex, Claude Code, and Cursor docs are linked from the docs index.
- Launch posts are drafted in [launch-posts.md](launch-posts.md).
- Social preview source exists under `docs/assets/`.
- Remote GitHub topics, social preview upload, and issue creation require repository settings access and should be verified on GitHub after this local package lands.
