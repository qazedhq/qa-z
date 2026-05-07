# QA-Z Launch Posts

These drafts keep the launch message problem-first instead of release-number-first.

## Hacker News

Title:

```text
Show HN: QA-Z - deterministic QA gates for AI-generated code
```

Body:

```text
AI coding agents can generate code quickly, but I kept running into the same problem: after the agent changes code, I still need deterministic evidence before merging.

QA-Z is a local CLI that turns agent changes into QA contracts, fast checks, Semgrep-backed deep checks, review packets, repair prompts, and post-repair verification artifacts.

It does not call an LLM or edit code by itself. It is designed to sit around tools like Codex, Claude Code, Cursor, aider, OpenHands, or Goose and answer: should this change be merged, and if not, what should the agent fix next?
```

## X / LinkedIn

```text
AI coding agents are great at writing code.

But before you merge their changes, you need evidence:
- what changed
- what was tested
- what failed
- what security checks found
- what the agent should fix next
- whether the repair actually improved things

I built QA-Z for that.

It is a deterministic QA layer for Codex, Claude Code, Cursor, and other coding-agent workflows.

GitHub: https://github.com/qazedhq/qa-z
```

## Blog

Title options:

- I built a safety belt for AI-generated code
- AI coding agents need QA gates, not vibes
- Stop merging AI code without deterministic evidence
- QA-Z: deterministic QA gates for coding agents

Opening:

```text
Coding agents write code fast. The hard part is deciding whether that code is safe to merge. QA-Z is a local, deterministic QA layer that turns agent changes into contracts, checks, repair prompts, and verification evidence.
```
