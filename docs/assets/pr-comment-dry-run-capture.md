# PR Comment Dry-Run Capture

This is a sanitized textual capture, not a private repository screenshot.

Template:

```text
templates/.github/workflows/qa-z-pr-comment.yml
```

Default environment:

```text
QA_Z_POST_PR_COMMENT=false
```

Expected workflow behavior:

```text
Run QA-Z gate                         -> executed
Build optional PR comment body         -> skipped
Post optional PR comment               -> skipped
GitHub pull request comment created    -> no
Review surface                         -> job summary + uploaded artifacts
```

Why the comment steps are skipped:

```text
if: always() && env.QA_Z_POST_PR_COMMENT == 'true'
```

Private data intentionally omitted:

- repository-private file contents
- user emails
- tokens
- secret names or values
- internal branch names not needed for the example
- real PR text or comments
