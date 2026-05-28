# qa-z init

Use `qa-z init` when adapting QA-Z to a repository for the first time. The
command writes a starter `qa-z.yaml`, a `qa/contracts/README.md`, and optional
agent or GitHub Actions starter files.

## Auto Profile

Start with a dry run so QA-Z can explain the profile it would choose:

```bash
qa-z init --profile auto --dry-run
```

The auto detector reports:

- selected profile: `python`, `typescript`, `nextjs`, `monorepo`, `mixed`, or `unknown`
- confidence: `high`, `medium`, or `low`
- evidence files such as `pyproject.toml`, `package.json`, `next.config.mjs`, `pnpm-workspace.yaml`, `turbo.json`, `apps/`, or `packages/`
- activated check assumptions, such as Python fast checks, TypeScript fast checks, smart selection, and Semgrep deep checks
- warnings when repo signals are mixed or no known setup files are present
- the next command to run

The dry-run output starts with a readable decision block before the legacy
lowercase compatibility lines:

```text
QA-Z init profile detection: nextjs
Recommended profile: nextjs
Confidence: high
Evidence:
- package.json
- next.config.js
Activated checks:
- Next.js TypeScript surface
- TypeScript fast checks
- Semgrep deep checks
Next:
- qa-z init --profile nextjs
```

When the dry run looks right, write the starter files:

```bash
qa-z init --profile auto --with-agent-templates
```

If `qa-z.yaml` already exists, init does not overwrite it. The existing config
remains the source of truth; use `qa-z init --profile auto --dry-run` to compare
repo signals with the current config before editing by hand.

## Profiles

`python` enables Python fast-check surfaces and Semgrep deep checks.

`typescript` enables TypeScript fast-check surfaces and Semgrep deep checks.

`nextjs` uses the TypeScript check surface and records the project profile as
Next.js when `package.json` or `next.config.*` indicates a Next.js app.

`monorepo` uses Python and TypeScript check surfaces with smart fast selection.
It is selected from workspace and layout signals such as `pnpm-workspace.yaml`,
`turbo.json`, `apps/`, `packages/`, or multiple package manifests.

`mixed` is for Python and TypeScript signals without clear monorepo layout.
Review the generated config before treating it as a full workspace policy.

`unknown` keeps a conservative starter config when QA-Z cannot identify a repo
shape. It is a prompt to inspect the repo rather than a release or readiness
claim.

## Boundaries

`qa-z init` is local setup only. It does not upload packages, publish to PyPI or
TestPyPI, create tags, create GitHub Releases, deploy, commit, push, post
comments, call live model APIs, or run coding agents.

Production PyPI is not published in this repository state. Use the GitHub source
install path documented in the quickstart until docs explicitly say otherwise.
