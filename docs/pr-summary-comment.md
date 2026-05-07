# PR Summary And Optional Comment UX

The default QA-Z GitHub workflow writes a job summary and uploads artifacts. It does not post comments.

For teams that want visible PR feedback, use the opt-in template:

```text
templates/.github/workflows/qa-z-pr-comment.yml
```

## Comment Shape

```text
QA-Z Review

Verdict: do not merge yet

Fast checks:
- py_test failed
- py_type passed

Deep checks:
- 2 blocking Semgrep findings

Repair prompt:
qa-z repair-prompt --from-run .qa-z/runs/pr --adapter codex
```

## Safety Boundary

The template requires `pull-requests: write` and is disabled by default through `QA_Z_POST_PR_COMMENT=false`.

Enable it only after maintainers accept bot-comment behavior for that repository.
