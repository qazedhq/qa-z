# QA-Z docs

Use the root [README](../README.md) for public onboarding and the shortest tryout path. These docs hold the deeper contracts, artifact schemas, and operator-maintenance notes.

## Start here

| Document | Purpose |
| --- | --- |
| [Quickstart](quickstart.md) | Five-minute local path from install to QA evidence |
| [Comparison](comparison.md) | How QA-Z fits around coding agents, Semgrep, and test tools |
| [GitHub Action](github-action.md) | Pull request gate setup using the shipped workflow and composite action |
| [Use with Codex](use-with-codex.md) | Codex handoff loop using QA-Z repair prompts |
| [Use with Claude Code](use-with-claude-code.md) | Claude Code handoff loop using the same deterministic artifacts |
| [Use with Cursor](use-with-cursor.md) | Cursor workflow using QA-Z before merge |
| [Launch package](launch-package.md) | Repository topics, social preview, release checklist, and good-first-issue seeds |
| [Launch checklist](../docs/launch-checklist.md) | Phase 0 to Phase 4 execution plan, top 10 actions, blockers, and no-go boundaries |
| [Public roadmap](../docs/public-roadmap.md) | Public roadmap from alpha polish through category leadership |
| [Package publish plan](../docs/package-publish-plan.md) | TestPyPI, PyPI, pipx, and uv install path |
| [Use with Semgrep](../docs/use-with-semgrep.md) | Semgrep-backed deep gate setup and SARIF expectations |
| [PR summary comment](../docs/pr-summary-comment.md) | Optional pull request comment template and permission boundary |
| [Agent Merge Safety Benchmark](../docs/agent-merge-safety-benchmark.md) | Public benchmark shape for agent change, QA-Z detection, repair, and verification |
| [OpenSSF Scorecard](../docs/scorecard.md) | Security trust surface and scorecard workflow notes |
| [Community distribution](../docs/community-distribution.md) | HN, X, LinkedIn, Reddit, Dev.to, Hashnode, and awesome-list launch plan |
| [Hosted demo](hosted-demo.md) | Hosted-demo scope that stays local-first and honest |
| [Docs site](docs-site.md) | Docs-site IA for the public category surface |
| [Case studies](case-studies.md) | Real-world walkthrough format for public adoption proof |
| [Monthly benchmark report](monthly-benchmark-report-template.md) | Repeatable benchmark-report template |
| [Launch posts](launch-posts.md) | Draft launch copy for Hacker News, X, LinkedIn, and blog posts |
| [Product direction](product/PRODUCT_DIRECTION.md) | Canonical product context, MVP goal, production goal, workflows, scope, gates, and open questions |
| [V8 handoff](product/V8_HANDOFF.md) | Concise operational product context for production-readiness self-improvement loops |
| [Product decisions](product/PRODUCT_DECISIONS.md) | Confirmed decisions, inferred decisions, deferred decisions, non-goals, and open questions |
| [Artifact schema v1](artifact-schema-v1.md) | Artifact formats and field-level contracts |
| [Repair sessions](repair-sessions.md) | Local repair-session packaging and handoff model |
| [Pre-live executor safety](pre-live-executor-safety.md) | Safety boundaries before any live executor integration |
| [Generated vs frozen evidence policy](generated-vs-frozen-evidence-policy.md) | Rules for local runtime artifacts, benchmark evidence, and frozen fixtures |
| [Current-truth maintenance anchors](current-truth-maintenance-anchors.md) | Internal operator-contract anchors and release-continuity guard text |
| [Architecture](architecture.md) | Contributor map for CLI, config, runners, reporters, repair, verification, executor, benchmark, and autonomy layers |
| [Benchmarking](benchmarking.md) | Seeded benchmark fixtures, result outputs, and benchmark evidence expectations |
| [Demo script](demo-script.md) | Text-only demo flow using real CLI commands |
| [Demo output](demo-output.md) | Captured local FastAPI demo output for README preview evidence |

## Examples

| Path | Purpose |
| --- | --- |
| [../qa-z.yaml.example](../qa-z.yaml.example) | Full public example configuration |
| [../examples/README.md](../examples/README.md) | Runnable demo index and placeholder boundary |
| [../examples/agent-auth-bug/](../examples/agent-auth-bug/) | Five-minute "AI auth bug caught by QA-Z" demo |
| [../examples/fastapi-agent-bug/](../examples/fastapi-agent-bug/) | FastAPI auth-bug walkthrough for the launch story |
| [../examples/typescript-agent-bug/](../examples/typescript-agent-bug/) | TypeScript permission-bug walkthrough for the launch story |
| [../examples/typescript-demo/](../examples/typescript-demo/) | Runnable TypeScript fast-gate demo |
| [../examples/fastapi-demo/](../examples/fastapi-demo/) | Dependency-light Python/FastAPI demo |
| [../examples/nextjs-demo/](../examples/nextjs-demo/) | Honest placeholder boundary for a future Next.js demo |
