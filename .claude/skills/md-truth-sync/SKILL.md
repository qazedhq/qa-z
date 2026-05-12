---
name: md-truth-sync
description: Use when AGENTS.md, CLAUDE.md, README, handoffs, reports, release notes, or docs may be stale after code or evidence changes.
---

# Markdown Truth Sync

1. Identify source-of-truth docs.
2. Identify generated or historical docs.
3. Check changed files and validation output.
4. Update only docs that became false or incomplete.
5. Add one recurring-failure note if the same mistake happened twice.
6. Keep instruction files short; move long details to `docs/agent/*.md`.
