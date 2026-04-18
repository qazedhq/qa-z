# P63-P66 Selected Task Status Detail Plan

1. Add failing autonomy tests for additive `latest_selected_task_details` and the matching plain-text status section.
2. Shape compact selected-task details directly from `selected_tasks.json` inside `load_autonomy_status()`.
3. Render those compact task details in the human-readable autonomy status output without changing the existing selected-id list.
4. Update README, schema docs, and current-truth tests, then rerun focused and full validation plus a real-repo status check.
