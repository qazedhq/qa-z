# Issue Tracker: GitHub

Matt Pocock skills that publish, read, or triage issues use GitHub Issues for this repo.

Repository: `qazedhq/qa-z`

## Conventions

- Create issues with `gh issue create --repo qazedhq/qa-z --title "..." --body-file <file>`.
- Read issues with `gh issue view <number> --repo qazedhq/qa-z --comments`.
- List issues with `gh issue list --repo qazedhq/qa-z --state open --json number,title,body,labels,comments`.
- Comment with `gh issue comment <number> --repo qazedhq/qa-z --body-file <file>`.
- Apply or remove labels with `gh issue edit <number> --repo qazedhq/qa-z --add-label "..."` or `--remove-label "..."`.

When a skill says "publish to the issue tracker", create a GitHub issue in this repository.
