# QA-Z Launch Kit

Status: repo-local launch/growth kit only. Draft copy below is not published,
posted, submitted, or scheduled from this document.

Boundary: No PyPI live claim. TestPyPI/PyPI publish has not happened yet, so the
current install path is GitHub source install only.

## Product Description

One-line product description:

```text
Make AI coding safe to merge.
```

Short product description:

```text
QA-Z is a deterministic merge-safety layer for AI-generated code. It turns
agent changes into local checks, SARIF, a guard verdict, a repair prompt, and a
post-repair verification report so reviewers can decide what is safe to merge.
```

## Who Should Try This

- Codex users who want deterministic evidence before accepting generated code.
- Cursor users who need a local guard before merging AI-authored changes.
- Claude Code users who want repair prompts grounded in local artifacts.
- aider/OpenHands users who want a model-agnostic QA handoff loop.
- teams reviewing AI-generated PRs in GitHub Actions.

## What QA-Z Is Not

- not another coding agent
- not an LLM judge
- not a PyPI package yet
- not a replacement for tests/Semgrep/human review
- not a tool that edits target repositories, mutates branches, commits, pushes,
  tags, creates GitHub Releases, deploys, posts externally, or comments on PRs
  by itself

## Current Install Path

GitHub source install command:

```bash
pipx install git+https://github.com/qazedhq/qa-z.git
```

Do not replace this with the package-registry shortcut or a PyPI/TestPyPI
command until a separate release-owner publish path is approved and executed.

## Core Demo Story

Use the current auth-bug demo as the launch proof:

1. An AI-generated auth change weakens owner checks.
2. `qa-z demo auth-bug` produces a risky local scenario.
3. `qa-z guard --from-run latest --adapter codex` returns `do_not_merge`.
4. The visible reason is `auth/owner-check risk`.
5. QA-Z writes a scoped repair prompt for an external executor or human.
6. After the included repair, `qa-z verify` reports `verify improved`.

Keep the public story simple:

```text
AI-generated auth change -> do_not_merge -> repair prompt -> verify improved
```

## GitHub Action Adoption

The next activation step after the demo is the 5-minute PR gate in
`docs/github-action.md`.

Default permissions stay minimal:

```yaml
permissions:
  contents: read
  actions: read
```

SARIF upload is opt-in with `security-events: write`.
PR comments and bot comments are opt-in through a separate template; they are
not enabled by the minimal guard action.

## Draft Copy

Draft only. Do not post from this document.

### X / LinkedIn Draft

```text
Coding agents write code fast.

QA-Z helps you decide if that code is safe to merge.

It is a local deterministic layer for AI-generated PRs: checks, SARIF, a guard
verdict, a repair prompt, and verify-after-repair evidence.

Try the auth-bug demo:
pipx install git+https://github.com/qazedhq/qa-z.git
qa-z demo auth-bug

Repo: https://github.com/qazedhq/qa-z
```

### Reddit Draft

```text
I am building QA-Z, a local merge-safety layer for AI-generated code.

It is not another coding agent and it does not call an LLM to judge code. The
goal is deterministic evidence: local checks, Semgrep-backed deep checks, SARIF,
a guard verdict, repair prompts, and verification after a repair.

The best demo right now is an auth-bug scenario where an agent-style change
weakens an owner check. QA-Z returns do_not_merge, points at the auth/owner-check
risk, writes a repair prompt, and then verify reports improved after the fix.

Current install path is GitHub source install only. PyPI/TestPyPI publish has not
happened yet.
```

### Hacker News Draft

```text
Show HN: QA-Z - Make AI coding safe to merge

QA-Z is a local deterministic QA layer for AI-generated code. It does not call
live agents, mutate branches, or use an LLM as the merge judge. It turns agent
changes into checks, SARIF, a guard verdict, repair prompts, and verification
evidence.

The launch demo is an auth-bug flow: QA-Z catches an owner-check risk, returns
do_not_merge, generates a repair prompt, and verifies the repaired candidate as
improved.

Current status: GitHub source install only. No package registry publish has
happened yet.
```

## Launch Order

1. soft launch on X/LinkedIn with the draft copy above.
2. collect feedback from people who try the auth-bug demo or GitHub Action.
3. Show HN only after README, demo, and troubleshooting copy survive feedback.
4. Reddit cautiously in relevant communities, with the no-agent/no-LLM-judge
   boundary up front.
5. update README/FAQ from questions that repeat.
6. revisit TestPyPI/PyPI decision after release-owner approval, credential
   boundary review, final SHA proof, and no-upload smoke evidence are current.

## FAQ / Expected Questions

### Is QA-Z a coding agent?

No. QA-Z evaluates, summarizes, gates, and prepares repair handoff evidence. It
does not silently remediate target repositories.

### Does QA-Z use an LLM to decide merge safety?

No. QA-Z is deterministic and local-first. It records checks, findings, guard
verdicts, repair prompts, and verification evidence.

### Can I install it from PyPI?

No. No PyPI live claim is valid right now. Use GitHub source install until a
separate publish approval and execution path exists.

### Does the GitHub Action need write permissions?

Not for the minimal PR gate. Start with `contents: read` and `actions: read`.
SARIF and comments are separate opt-in paths.

### Does QA-Z replace tests, Semgrep, or review?

No. QA-Z wraps those signals into merge evidence and repair guidance. It does
not replace tests/Semgrep/human review.

### What is the fastest proof to show?

Run the auth-bug demo, show `do_not_merge`, point at the `auth/owner-check risk`,
open the repair prompt, then show `verify improved` after the fixed candidate.

## Explicit Non-Actions

This launch kit does not perform release execution. It does not publish to
TestPyPI or PyPI, load registry credentials, bump `pyproject.toml`, create a tag,
create a GitHub Release, deploy, post externally, mutate GitHub settings, call a
live model API, or add generated `.qa-z/**` runtime artifacts to source.
