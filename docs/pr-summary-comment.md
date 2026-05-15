# PR Summary And Optional Comment UX

The default QA-Z GitHub workflow writes a job summary and uploads artifacts. It does not post comments.

For teams that want visible PR feedback, use the opt-in template:

```text
templates/.github/workflows/qa-z-pr-comment.yml
```

## Default Dry Run

The template defaults to:

```yaml
QA_Z_POST_PR_COMMENT: "false"
```

With the default value, the QA-Z gate can still produce job summaries and artifacts, but the optional comment body and post-comment steps are skipped.

Expected dry-run behavior:

- no pull request comment is created
- no GitHub issue/comment API call is made
- QA-Z job summary and run artifacts remain the review surface
- maintainers can inspect the workflow run before enabling comment posting

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

## Dry-Run Capture

See `docs/assets/pr-comment-dry-run-capture.md` for a sanitized capture of the default non-posting behavior.

## Permission Tradeoff

`pull-requests: write` is required only for the optional comment-posting step. It is broader than the default QA-Z summary workflow, so maintainers should enable this template only when they explicitly accept bot-comment behavior.

Keep `QA_Z_POST_PR_COMMENT=false` until the repository owner approves the permission tradeoff.

## Safety Boundary

The template requires `pull-requests: write` and is disabled by default through `QA_Z_POST_PR_COMMENT=false`.

Enable it only after maintainers accept bot-comment behavior for that repository.
