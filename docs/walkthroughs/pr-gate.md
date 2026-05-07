# Walkthrough: Pull Request Gate

Install the QA-Z workflow template:

```text
templates/.github/workflows/vibeqa.yml
```

The gate preserves artifacts before failing the job:

- fast summary;
- deep summary;
- review packet;
- repair prompt;
- GitHub job summary;
- SARIF when available.

For optional visible PR feedback, use [../pr-summary-comment.md](../pr-summary-comment.md).
