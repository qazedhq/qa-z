# QA-Z Public Roadmap

QA-Z is aiming to become the AI Code QA layer: deterministic merge evidence before AI-generated code lands.

## 0 to 100 stars

- Keep the README product-first.
- Ship the agent-auth-bug demos.
- Publish the social preview.
- Open clear good-first issues.
- Share the Show HN and social launch drafts.

## 100 to 1,000 stars

- Prepare TestPyPI and PyPI publishing.
- Keep `pipx` and `uv tool install` paths working from Git tags.
- Add a second recorded demo.
- Strengthen GitHub Actions templates.
- Publish adapter docs for Codex, Claude Code, Cursor, and Semgrep.

## 1,000 to 5,000 stars

- Add five real repository walkthroughs.
- Publish three Before/After AI bug caught articles.
- Open GitHub Discussions or Discord.
- Submit focused PRs to AI coding, testing, and DevSecOps awesome lists.
- Add OpenSSF Scorecard and security trust notes.

## 5,000 to 10,000 stars

- Provide a stable GitHub Action entry point.
- Add optional PR comment behavior.
- Improve SARIF/code-scanning examples.
- Keep monorepo, TypeScript-first, and security-focused docs/demos current.
- Publish the Agent Merge Safety Benchmark.

## 10,000 to 30,000 stars

- Provide a hosted demo without requiring QA-Z Cloud.
- Publish a public agent repair quality leaderboard.
- Add integrations for Codex, Claude Code, Cursor, aider, OpenHands, and Goose.
- Launch an official docs site.
- Publish monthly benchmark reports.
- Collect 2 to 3 company use cases.

## Propose A Roadmap Item

The monorepo quickstart path is documented in `docs/quickstart.md` and should remain deterministic/local.

Use the GitHub issue template:

```text
.github/ISSUE_TEMPLATE/roadmap_proposal.yml
```

A roadmap proposal must include:

- user impact;
- evidence from issues, docs, artifacts, CI runs, or examples;
- deterministic validation commands;
- explicit non-goals;
- generated-artifact policy;
- whether the proposal affects docs, CI, examples, package readiness, benchmarks, or integrations.

Roadmap proposals do not approve package publishing, tags, releases, deployments, live model execution, bot comments, branch mutation, or hosted automation. Those require separate maintainer approval and the appropriate release or safety handoff.

Community example proposals should also follow `docs/community-distribution.md`, including the required evidence, validation commands, privacy rules, and generated-artifact policy.

## Current Non-Goals

- QA-Z does not autonomously edit code.
- QA-Z does not call live model APIs.
- QA-Z does not replace deterministic pass/fail checks with LLM-only judgment.
