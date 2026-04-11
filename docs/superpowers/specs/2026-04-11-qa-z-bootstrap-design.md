# QA-Z Bootstrap Design

**Date:** 2026-04-11

## Goal

Bootstrap a public-facing `QA-Z` repository that positions the project as a Codex-first, model-agnostic QA control plane for coding agents. The first commit should feel like a serious open-source project, not a blank idea dump.

## Product Definition

`QA-Z` turns prompts, specs, issues, and diffs into executable QA contracts and merge gates for coding agents.

The repository should show four things immediately:

1. A clear public narrative in the README.
2. Agent operating rules in `AGENTS.md`.
3. A concrete policy surface through `qa-z.yaml.example`.
4. An executable bootstrap through a minimal Python CLI, templates, and CI.

## Recommended Approach

Use a "docs plus runnable scaffold" bootstrap:

- Keep the product story front and center with opinionated docs.
- Add a thin Python package so the project already has a real command surface.
- Make `init` useful now, even if deeper commands are placeholders.
- Ship Codex and Claude templates so the repo demonstrates its integration story.
- Include a GitHub workflow for this repo and a template workflow for downstream users.

This approach is the best balance between credibility and scope. A docs-only repo feels speculative; a full engine implementation would sprawl too early.

## Non-Goals For This Bootstrap

- No real diff parser yet.
- No contract extraction engine yet.
- No actual lint/typecheck/test orchestration yet.
- No adapter runtime for Codex or Claude yet.

The first version should promise the architecture and prove the workflow surface, not fake deep behavior.

## Repository Shape

The bootstrap should create the following structure:

```text
.
|- README.md
|- AGENTS.md
|- LICENSE
|- .gitignore
|- pyproject.toml
|- qa-z.yaml.example
|- docs/
|  |- mvp-issues.md
|  `- superpowers/
|     |- plans/
|     `- specs/
|- qa/
|  `- contracts/
|- src/qa_z/
|  |- __init__.py
|  |- __main__.py
|  |- cli.py
|  |- config.py
|  |- planner/
|  |- contracts/
|  |- runners/
|  |- reporters/
|  |- adapters/
|  `- plugins/
|- tests/
|- templates/
|  |- AGENTS.md
|  |- CLAUDE.md
|  |- .claude/skills/qa-guard/SKILL.md
|  `- .github/workflows/vibeqa.yml
|- .github/
|  |- codex/prompts/review.md
|  `- workflows/
|- examples/
`- benchmark/
```

## CLI Scope

The Python CLI should expose:

- `qa-z init`
- `qa-z plan`
- `qa-z fast`
- `qa-z deep`
- `qa-z review`
- `qa-z repair-prompt`

Only `init` must perform file-system work in this bootstrap. The others can return structured "planned capability" guidance so the interface is stable while implementation catches up.

## Configuration Surface

`qa-z.yaml.example` should model the long-term control-plane concepts:

- project languages and entrypoints
- contract sources
- fast and deep checks
- critical paths and escalation rules
- output reporters
- agent adapter toggles

## Templates

Templates should demonstrate how QA-Z plugs into agent workflows:

- `templates/AGENTS.md` for Codex-facing rules
- `templates/CLAUDE.md` for Claude Code guidance
- `templates/.claude/skills/qa-guard/SKILL.md` for reusable QA enforcement
- `templates/.github/workflows/vibeqa.yml` for CI integration
- `.github/codex/prompts/review.md` and `.github/workflows/codex-review.yml` for this repo's own Codex-first posture

## Testing Strategy

Use TDD for the bootstrap CLI:

1. Write CLI tests for subcommand registration and `init` behavior.
2. Verify they fail.
3. Implement the minimum code to pass.
4. Re-run tests.

The repository itself should be verifiable with `python -m pytest`.

## Success Criteria

The bootstrap is successful when:

- the repo tells a coherent story from the root README;
- the package installs locally with `pip install -e .`;
- `python -m pytest` passes;
- `python -m qa_z init` creates a starter config and contract directory in a temp repo;
- downstream contributors can see the intended next issues in `docs/mvp-issues.md`.
