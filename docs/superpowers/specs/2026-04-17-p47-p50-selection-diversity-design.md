# P47-P50 Selection Diversity Design

## Goal

Improve `select-next` so multi-task batches do not overfill with one fallback family when a comparable alternative family is available.

## Why now

Recent work reduced stale runtime-artifact backlog noise. That makes the remaining backlog more concentrated, which in turn exposes a smaller but real issue: `select-next --count 2` or `--count 3` can still choose near-identical cleanup tasks even when another family is close enough to be worth rotating in.

## Scope

- keep the existing recent-history penalty model
- add a light within-batch fallback-family penalty
- preserve same-family selection when no alternative family exists
- document the new behavior and pin it with tests

## Non-goals

- no probabilistic ranking
- no LLM-based selection
- no hard one-per-family cap

## Intended result

Selection stays score-driven, but becomes slightly more diverse within one batch when the next-best alternative family is materially comparable.
