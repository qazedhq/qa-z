# Agent Adapters

QA-Z is the merge-safety layer around coding agents. Agents and editors can
write code; QA-Z records deterministic evidence, prepares repair handoffs, and
verifies whether a candidate improved.

Run:

```bash
qa-z repair-prompt --from-run latest --adapter codex
```

Supported repair-prompt adapters:

| Adapter | Artifact | Use when |
| --- | --- | --- |
| `codex` | `.qa-z/runs/latest/repair/codex.md` | Codex is the repair executor |
| `claude` | `.qa-z/runs/latest/repair/claude.md` | Claude Code is the repair executor |
| `cursor` | `.qa-z/runs/latest/repair/cursor.md` | Cursor is the editor workflow |
| `aider` | `.qa-z/runs/latest/repair/aider.md` | aider is the patch executor |
| `openhands` | `.qa-z/runs/latest/repair/openhands.md` | OpenHands is the bounded task executor |
| `generic` | `.qa-z/runs/latest/repair/generic.md` | Another coding tool needs a neutral checklist |
| `human` | `.qa-z/runs/latest/repair/human.md` | A human reviewer needs a merge-safety checklist |

`legacy` remains available for the older generic `prompt.md` stdout shape. New
handoffs should prefer one of the adapter names above.

## Shared Contract

Every adapter Markdown prompt includes:

- objective;
- relevant evidence paths;
- repair targets;
- files and risks;
- forbidden actions;
- required validation;
- final report format;
- merge-safety boundaries.

The prompts always say not to claim success without validation. They point the
executor back to `qa-z verify --from-run <source-run>` after applying a repair.

## Boundaries

Adapter prompts are deterministic local files. They do not call agent APIs,
open editor sessions, post comments, commit, push, deploy, upload packages, or
create releases.

Changing `--adapter` changes presentation only. The normalized contract remains
`repair/handoff.json`, and QA-Z remains the judge of merge evidence.
