# Report Template Example Sync Design

## Goal

Keep QA-Z's public config example, downstream agent templates, and shipped examples aligned with the current alpha implementation without implying unlanded deep engines or live executor behavior.

## Problem

The repository has been hardening quickly. Core docs now describe the landed fast, deep, benchmark, autonomy, executor-bridge, executor-result, and dry-run surfaces, but some onboarding surfaces still carry older or too-broad language:

- `qa-z.yaml.example` and the built-in `EXAMPLE_CONFIG` still include placeholder deep-check names such as `property`, `mutation`, and `e2e_smoke` under the legacy `checks.deep` surface even though only configured Semgrep deep checks execute today.
- downstream templates describe a generic QA loop, but they do not yet name the current deterministic commands and live-free boundaries clearly.
- `examples/nextjs-demo/README.md` presents future TypeScript deep tools as a planned demo instead of an explicit placeholder that points users to the landed TypeScript fast demo.

Those are not core runtime bugs. They are current-truth risks: a new operator could infer that unsupported deep engines or richer template workflows already exist.

## Chosen Approach

Make a narrow sync pass across config, templates, examples, and reports.

1. Public config example
   - keep the landed `fast.checks` Python and TypeScript check examples
   - keep the landed `deep.checks` `sg_scan` Semgrep example
   - keep `checks.selection.max_changed_files` because runners still use it as a compatibility fallback
   - remove the unsupported legacy `checks.deep` placeholder list from the public and built-in examples

2. Agent templates
   - update `templates/AGENTS.md`, `templates/CLAUDE.md`, and `templates/.claude/skills/qa-guard/SKILL.md`
   - name the current deterministic loop: `plan`, `fast`, `deep`, `review`, `repair-prompt`, `repair-session`, `verify`, and `github-summary`
   - state that executor bridge/result workflows are handoff and return contracts, not live agent invocation

3. Examples
   - update `examples/nextjs-demo/README.md` to say it is an unwired placeholder
   - point users to `examples/typescript-demo` for the landed TypeScript fast gate
   - avoid listing future deep tools as if the example proves them

4. Reports
   - update current-state and roadmap wording so this sync pass is described as an ongoing maintenance category with the first template/example cleanup landed

## Non-Goals

- no new CLI behavior
- no new config parser behavior
- no rename of the existing workflow template path
- no live executor, scheduler, queue, branch, commit, push, or GitHub bot behavior
- no claim that property, mutation, Playwright, Stryker, or TypeScript deep automation exists

## Tests

Add current-truth tests that prove:

- public `qa-z.yaml.example` still matches built-in `EXAMPLE_CONFIG`
- the example config does not advertise unsupported legacy `checks.deep` engines
- the example config still contains the landed `deep.checks` `sg_scan` surface
- downstream templates mention current deterministic workflow commands and live-free executor boundaries
- the Next.js example README explicitly says it is not wired and does not advertise future deep tools as current coverage
