# QA-Z

> The safety belt for AI-generated code.

[![CI](https://github.com/qazedhq/qa-z/actions/workflows/ci.yml/badge.svg)](https://github.com/qazedhq/qa-z/actions/workflows/ci.yml)
![Status](https://img.shields.io/badge/status-alpha-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)
[![Release](https://img.shields.io/github/v/release/qazedhq/qa-z?include_prereleases&label=release)](https://github.com/qazedhq/qa-z/releases/tag/v0.9.8-alpha)

Coding agents write code. QA-Z tells you if that code is safe to merge.

QA-Z = QA from A to Z for agent-generated code. It turns agent changes into deterministic merge evidence: QA contracts, fast checks, Semgrep-backed deep checks, review packets, repair prompts, post-repair verification, GitHub summaries, SARIF, and benchmark artifacts.

> Should this change be merged, and if not, what should the agent fix next?

```bash
qa-z plan --diff changes.diff --title "Review agent change" --slug agent-change --overwrite
qa-z fast
qa-z deep --from-run latest
qa-z review --from-run latest
qa-z repair-prompt --from-run latest --adapter codex
```

QA-Z does not replace coding agents. QA-Z makes Codex, Claude Code, Cursor, aider, OpenHands, Goose, and similar tools safer to use before merge.

## Five-Minute Demo

Try the "AI wrote a bad auth change. QA-Z caught it." demo:

```bash
cd examples/agent-auth-bug
qa-z plan --title "AI auth bug caught by QA-Z" --issue issue.md --spec spec.md --slug ai-auth-bug --overwrite
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z review --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex
```

What the demo shows:

- Agent changed auth logic.
- Tests catch the unsafe access path.
- Optional Semgrep deep checks flag the risky pattern.
- QA-Z writes a repair prompt with deterministic evidence.
- After the fix, `qa-z verify` can compare baseline and candidate run artifacts.

For the full copy/paste script, see [docs/demo-script.md](docs/demo-script.md). For the short onboarding path, see [docs/quickstart.md](docs/quickstart.md).

## Quickstart

QA-Z is alpha software. Install the prerelease from GitHub:

```bash
pipx install "git+https://github.com/qazedhq/qa-z.git@v0.9.8-alpha"
```

Or with uv:

```bash
uv tool install "git+https://github.com/qazedhq/qa-z.git@v0.9.8-alpha"
```

Contributor fallback:

```bash
python -m pip install -e .[dev]
```

Install Semgrep when running the documented deep QA gate locally:

```bash
python -m pip install semgrep
```

Initialize a repository and run the smallest local loop:

```bash
qa-z init --profile python --with-agent-templates --with-github-workflow
qa-z doctor
qa-z plan --title "Review recent agent change" --slug agent-change --overwrite
qa-z fast
qa-z review --from-run latest
qa-z repair-prompt --from-run latest --adapter codex
```

If the console script is not on PATH, use the module fallback:

```bash
python -m qa_z fast
```

The output is local and artifact-first. Look under `.qa-z/runs/` for run evidence.

## Why QA-Z?

Most coding agents stop at "I changed the code."

QA-Z adds the missing QA layer:

- What changed?
- What should be tested?
- Did fast checks pass?
- Did deep checks find risks?
- What should the agent fix next?
- Did the repair actually improve the result?

## Comparison

| Tool | Writes code | Runs checks | Produces repair prompt | Verifies repair | Model-agnostic QA evidence |
| --- | ---: | ---: | ---: | ---: | ---: |
| Codex | yes | partial | partial | partial | no |
| Claude Code | yes | partial | partial | partial | no |
| Cursor | yes | partial | partial | partial | no |
| Semgrep | no | yes | no | no | partial |
| pytest/ruff/mypy | no | yes | no | no | no |
| QA-Z | no | yes | yes | yes | yes |

QA-Z does not autonomously edit code. It creates deterministic evidence and repair instructions around the tools you already use.

## Core Workflow

```text
init -> plan -> fast -> deep -> review -> repair-prompt -> external repair -> verify -> github-summary
```

## Core Commands

| Command | What it does |
| --- | --- |
| `qa-z init` | Create starter QA-Z config and optional templates |
| `qa-z doctor` | Validate config shape and launch readiness |
| `qa-z plan` | Generate a QA contract from issue, spec, or diff input |
| `qa-z fast` | Run deterministic fast checks |
| `qa-z deep` | Run configured Semgrep deep checks |
| `qa-z review` | Render a review packet from run artifacts |
| `qa-z repair-prompt` | Generate Codex, Claude, or handoff repair prompts |
| `qa-z verify` | Compare baseline and candidate run artifacts |

## Advanced Commands

| Command | What it does |
| --- | --- |
| `qa-z repair-session` | Package a local repair workflow |
| `qa-z github-summary` | Render GitHub Actions summary Markdown |
| `qa-z benchmark` | Run seeded QA-Z benchmark fixtures |
| `qa-z self-inspect` | Inspect QA-Z artifacts and surface improvement tasks |
| `qa-z select-next` | Select the next self-improvement backlog tasks |
| `qa-z backlog` | Print the current QA-Z improvement backlog |
| `qa-z autonomy` | Run deterministic self-improvement planning loops |
| `qa-z executor-bridge` | Package a repair session for an external executor |
| `qa-z executor-result` | Ingest an external executor result for verification |

## Artifacts

| Path | Purpose |
| --- | --- |
| `.qa-z/runs/` | Fast and deep run evidence |
| `.qa-z/runs/latest/review/` | Review packet output |
| `.qa-z/runs/latest/repair/` | Repair prompt and handoff output |
| `.qa-z/runs/latest/deep/results.sarif` | Deep-check SARIF output |
| `.qa-z/sessions/` | Local repair session packages |
| `.qa-z/executor/` | External executor bridge packages |
| `.qa-z/executor-results/` | Returned executor result ingest artifacts |
| `.qa-z/improvement/` | Self-inspection and backlog artifacts |
| `.qa-z/loops/` | Autonomy planning loop artifacts |

Root `.qa-z/**` is local by default and should normally stay out of release commits.

## GitHub Action

Use the shipped workflow template to add QA-Z to a pull request gate:

```yaml
- name: Run QA-Z
  uses: qazedhq/qa-z/.github/actions/qa-z@v0.9.8-alpha
```

Until the standalone action is published, copy [templates/.github/workflows/vibeqa.yml](templates/.github/workflows/vibeqa.yml) or follow [docs/github-action.md](docs/github-action.md).

## What QA-Z Is Not

QA-Z is not:

- a coding agent
- an autonomous code editor
- a live Codex, Claude, Cursor, or model runtime
- a queue, scheduler, or remote orchestrator
- an LLM-only judge replacing deterministic checks
- a tool that commits, pushes, or posts GitHub comments by itself

QA-Z is the QA layer around those workflows.

## Status

QA-Z is alpha software. The current package metadata targets `0.9.8a0`, published in docs as `v0.9.8-alpha`.

Deep QA automation currently centers on Semgrep-backed checks and deterministic local artifacts. Codex and Claude support is adapter-oriented: QA-Z writes handoff material for external tools instead of calling live model APIs.

## Docs

- [Quickstart](docs/quickstart.md)
- [Comparison](docs/comparison.md)
- [GitHub Action](docs/github-action.md)
- [Use with Codex](docs/use-with-codex.md)
- [Use with Claude Code](docs/use-with-claude-code.md)
- [Use with Cursor](docs/use-with-cursor.md)
- [Launch package](docs/launch-package.md)
- Growth package: [launch checklist](docs/launch-checklist.md), [roadmap](docs/public-roadmap.md), [publish plan](docs/package-publish-plan.md), [Semgrep](docs/use-with-semgrep.md), [PR comments](docs/pr-summary-comment.md), [benchmark](docs/agent-merge-safety-benchmark.md), [scorecard](docs/scorecard.md), [distribution](docs/community-distribution.md)
- [Launch posts](docs/launch-posts.md)
- [Product direction](docs/product/PRODUCT_DIRECTION.md)
- [V8 handoff](docs/product/V8_HANDOFF.md)
- [Product decisions](docs/product/PRODUCT_DECISIONS.md)
- [Artifact schema v1](docs/artifact-schema-v1.md)
- [Repair sessions](docs/repair-sessions.md)
- [Generated vs frozen evidence policy](docs/generated-vs-frozen-evidence-policy.md)
- [Current-truth maintenance anchors](docs/current-truth-maintenance-anchors.md)
- [Architecture](docs/architecture.md)
- [Benchmarking](docs/benchmarking.md)
- [Demo script](docs/demo-script.md)
- [Demo output](docs/demo-output.md)
- [Docs index](docs/README.md)
- [Example config](qa-z.yaml.example)
- [Examples index](examples/README.md)

If QA-Z helps you trust AI-generated code before merging, star the repo to follow the alpha.

## License

Apache-2.0
