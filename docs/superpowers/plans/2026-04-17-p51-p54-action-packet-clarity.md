# P51-P54 Action Packet Clarity Plan

1. Add failing autonomy tests for recommendation-aware cleanup and integration action packets.
2. Extend `action_for_task()` with deterministic recommendation-specific commands and compact `context_paths`.
3. Render the richer action packets in autonomy loop plans and document the additive action fields in README and schema docs.
4. Run focused autonomy tests, then full repository validation and a fresh self-inspect/select-next check.
