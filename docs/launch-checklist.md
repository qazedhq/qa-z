# QA-Z 30k Star Launch Checklist

This checklist maps the full growth brief into repository-owned surfaces. Items that require GitHub settings, external accounts, or package registries are tracked as external blockers rather than silently marked complete.

## Positioning

- Primary: `QA-Z is the safety belt for AI-generated code.`
- Direct: `Coding agents write code. QA-Z tells you if that code is safe to merge.`
- Strong: `Stop trusting AI code blindly. Run QA-Z before you merge it.`
- Category: `AI Code QA` / `Agent QA`.

## Phase 0 - 0 to 100 stars

1. GitHub prerelease: present for `v0.9.8-alpha`; verify remotely before the next launch wave.
2. README product page: [../README.md](../README.md).
3. 10-second asciinema: [assets/qa-z-agent-auth-bug.cast](assets/qa-z-agent-auth-bug.cast).
4. Social preview: [assets/qa-z-social-preview.png](assets/qa-z-social-preview.png).
5. Topic optimization: [launch-package.md](launch-package.md).
6. Demo script: [demo-script.md](demo-script.md).
7. FastAPI agent bug: [../examples/fastapi-agent-bug/](../examples/fastapi-agent-bug/).
8. TypeScript agent bug: [../examples/typescript-agent-bug/](../examples/typescript-agent-bug/).
9. Good first issue guide: [../CONTRIBUTING.md](../CONTRIBUTING.md).
10. Issue seeds: [issues/good-first-issues.md](issues/good-first-issues.md).

## Phase 1 - 100 to 1,000 stars

- PyPI/TestPyPI plan: [package-publish-plan.md](package-publish-plan.md).
- `pipx` and `uv` install from Git: [quickstart.md](quickstart.md).
- Demo GIF/asciinema package: [demo-script.md](demo-script.md).
- GitHub Actions template: [github-action.md](github-action.md).
- Run QA-Z on your repo in 5 minutes: [quickstart.md](quickstart.md).
- Use with Codex, Claude Code, Cursor, and Semgrep: adapter docs in this directory.
- Hacker News, X, LinkedIn, and blog drafts: [launch-posts.md](launch-posts.md).

## Phase 2 - 1,000 to 5,000 stars

- Real-world walkthroughs: [walkthroughs/auth-bug.md](walkthroughs/auth-bug.md), [walkthroughs/pr-gate.md](walkthroughs/pr-gate.md), [walkthroughs/sarif-code-scanning.md](walkthroughs/sarif-code-scanning.md).
- Before/After article queue: [community-distribution.md](community-distribution.md).
- YouTube demo outline: [hosted-demo.md](hosted-demo.md).
- GitHub Discussions or Discord decision: [community-distribution.md](community-distribution.md).
- Awesome-list PR targets: [community-distribution.md](community-distribution.md).
- Comparison page: [comparison.md](comparison.md).
- OpenSSF Scorecard trust surface: [scorecard.md](scorecard.md).

## Phase 3 - 5,000 to 10,000 stars

- GitHub Action form: `.github/actions/qa-z/action.yml`.
- Optional PR comment template: [../templates/.github/workflows/qa-z-pr-comment.yml](../templates/.github/workflows/qa-z-pr-comment.yml).
- SARIF/code scanning walkthrough: [walkthroughs/sarif-code-scanning.md](walkthroughs/sarif-code-scanning.md).
- Monorepo and TypeScript-first demo slots: [public-roadmap.md](public-roadmap.md).
- Security-focused demo: [examples/fastapi-agent-bug](../examples/fastapi-agent-bug/).
- AI code review benchmark: [agent-merge-safety-benchmark.md](agent-merge-safety-benchmark.md).
- Weekly release cadence: [public-roadmap.md](public-roadmap.md).

## Phase 4 - 10,000 to 30,000 stars

- Hosted demo plan: [hosted-demo.md](hosted-demo.md).
- Public leaderboard: [agent-merge-safety-benchmark.md](agent-merge-safety-benchmark.md).
- Integrations with Codex, Claude Code, Cursor, aider, OpenHands, and Goose: [public-roadmap.md](public-roadmap.md).
- Official docs site: [docs-site.md](docs-site.md).
- Community examples: [community-distribution.md](community-distribution.md).
- Public roadmap: [public-roadmap.md](public-roadmap.md).
- Monthly benchmark report: [monthly-benchmark-report-template.md](monthly-benchmark-report-template.md).
- Enterprise use cases: [case-studies.md](case-studies.md).

## Week 1 - Repo polish

- README final product pass.
- Social preview image.
- Asciinema demo.
- Topic list.
- Agent auth examples.
- Quickstart and adapter docs.

## Week 2 - Install and demo

- TestPyPI/PyPI readiness plan.
- GitHub Action template.
- PR summary demo.
- Semgrep SARIF demo.
- Blog and 3-minute video outline.

## Week 3 - Distribution

- Hacker News Show HN.
- Reddit launch posts.
- X and LinkedIn threads.
- Dev.to / Hashnode article.
- Awesome-list PR queue.
- AI coding tools comparison.

## Week 4 - Credibility

- OpenSSF Scorecard workflow.
- Security, contributing, and code of conduct surfaces.
- Public roadmap.
- 20 good-first-issue seeds.
- 3 real-world walkthroughs.
- v0.9.9-alpha plan.

## Top 10 immediate actions

1. GitHub prerelease creation and verification.
2. README first sentence uses `The safety belt for AI-generated code`.
3. 10-second asciinema is available.
4. Social preview asset is ready.
5. `qa-z` CLI install flow is front-loaded.
6. `examples/agent-auth-bug` and `examples/fastapi-agent-bug` exist.
7. `docs/use-with-codex.md` exists.
8. `docs/use-with-claude-code.md` exists.
9. GitHub Action template is prepared.
10. Show HN, X, and LinkedIn launch posts are drafted.

## Killer feature candidates

- GitHub Action template.
- Optional PR comment bot.
- Copy-this-prompt-to-Codex block.
- Agent Merge Safety Benchmark.

## Do not do

- Do not ask for stars without value context.
- Do not describe every internal feature on the first screen.
- Do not lead with autonomy before trust is earned.

## External blockers

- GitHub topics and social preview upload require repository settings mutation.
- Public issues require GitHub issue-write permission.
- PyPI/TestPyPI require package registry credentials.
- Standalone `qazedhq/qa-z-action@v0` requires a separate repository or marketplace release.
