# AI Code Merge Checklist

- Is there a QA contract for the change?
- Did deterministic fast checks run?
- Did deep checks run for auth, security, data, API, infra, or public-surface risk?
- Are failed checks repaired without weakening gates?
- Did a post-repair verification run prove improvement?
- Are `.qa-z/runs/latest/guard/verdict.json` and review artifacts available?
- Is the merge verdict explicit?
