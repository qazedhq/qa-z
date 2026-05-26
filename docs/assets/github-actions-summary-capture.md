# GitHub Actions Summary Capture

This is a sanitized textual capture, not a private repository screenshot.

Expected GitHub Actions surface:

```text
Workflow run
Job: qa-z
Summary: QA-Z Summary
Artifact: qa-z-runs
Verdict: do_not_merge
Top blocked reason: py_type: mypy exited with code 1.
Pointers:
- .qa-z/runs/latest/guard/github-summary.md
- .qa-z/runs/latest/guard/verdict.md
- .qa-z/runs/latest/fast/summary.json
- .qa-z/runs/latest/deep/summary.json
- .qa-z/runs/latest/review/review.md
- .qa-z/runs/latest/repair/prompt.md
- .qa-z/runs/latest/repair/codex.md
- .qa-z/runs/latest/deep/results.sarif
Next commands:
- qa-z summary --from-run .qa-z/runs/latest
- qa-z repair-prompt --from-run .qa-z/runs/latest --adapter codex
- qa-z verify --from-run .qa-z/runs/latest
```

Reviewer path:

```text
1. Open the GitHub Actions workflow run.
2. Read the QA-Z Job Summary.
3. Download or inspect the qa-z-runs artifact when machine-readable evidence is needed.
4. Follow the fast, deep, review, repair, and guard artifact pointers before deciding whether to merge.
5. If SARIF upload is enabled, confirm the job grants security-events: write.
```

Private data intentionally omitted:

- private repository names
- private file contents
- real user emails
- token values
- secret names or values
- internal branch names not needed for the example
- real PR comments or customer data

Boundary:

```text
The summary is deterministic QA evidence.
It does not post a PR comment.
It does not commit, push, tag, release, deploy, publish packages, or call live model APIs.
It does not create generated .qa-z/** source artifacts for this capture.
```
