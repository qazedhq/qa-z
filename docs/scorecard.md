# OpenSSF Scorecard

QA-Z claims to improve trust in AI-generated code, so the repository should expose its own trust surface.

## Workflow

The repository includes:

```text
.github/workflows/scorecard.yml
```

It runs `ossf/scorecard-action` on a weekly schedule and supports manual dispatch.

## Why It Matters

OpenSSF Scorecard gives maintainers and adopters a reproducible view of repository security practices. For QA-Z, it supports the product message: deterministic evidence should apply to the tool itself, not only to user repositories.

## Local Follow-Up

Scorecard runs in GitHub Actions. Local validation is limited to YAML shape and repository tests.
