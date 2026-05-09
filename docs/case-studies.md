# Case Study Template

Use this template to document enterprise QA-Z evaluations with concrete evidence only. Do not invent customer names, adoption numbers, productivity claims, or security outcomes that were not measured.

## Case study title

`<Organization or redacted team> - <workflow QA-Z evaluated>`

## Context

- **Team or environment:** `<redacted enterprise team, repo type, or service area>`
- **Workflow:** `<agent-generated PR, security review, release gate, or other QA-Z use>`
- **QA-Z version or commit:** `<version, commit SHA, or release tag>`
- **Date range:** `<when the evaluation happened>`

## Non-goals

State what QA-Z did not automate or prove. For example:

- QA-Z did not replace human code review.
- QA-Z did not certify the whole codebase as secure.
- QA-Z did not measure organization-wide adoption.
- QA-Z did not claim time savings unless they were measured from the evaluation.

## Before evidence

Capture the starting point before QA-Z changed the review flow.

- **Baseline command(s):**

  ```bash
  <command run before QA-Z>
  ```

- **Baseline artifact(s):** `<paths, logs, SARIF files, CI links, or screenshots>`
- **Observed failure or gap:** `<specific issue found before QA-Z>`
- **Redactions applied:** `<secrets, private paths, hostnames, usernames, customer identifiers>`

## QA-Z runbook

Record the exact commands used so readers can reproduce the evaluation.

```bash
qa-z fast <path-or-command>
qa-z deep <path-or-command>
qa-z verify <candidate-or-artifact>
```

Include relevant configuration snippets, but redact tokens, credentials, internal URLs, private filesystem paths, and proprietary identifiers.

## After evidence

Describe only the measured result after QA-Z ran.

- **After command(s):**

  ```bash
  <command run after QA-Z or after the repair candidate>
  ```

- **After artifact(s):** `<paths, logs, SARIF files, CI links, or screenshots>`
- **Change in result:** `<before/after finding count, failing-to-passing check, improved verdict, or unchanged result>`
- **Reviewer decision:** `<merged, blocked, needs follow-up, or N/A>`

## Evidence table

| Evidence | Before | After | Source |
| --- | --- | --- | --- |
| Fast checks | `<result>` | `<result>` | `<log or CI link>` |
| Deep checks | `<result>` | `<result>` | `<SARIF or scanner output>` |
| Verify verdict | `<result>` | `<result>` | `<qa-z verify output>` |
| Human review | `<decision>` | `<decision>` | `<review note or ticket>` |

## Privacy and redaction checklist

- [ ] Secrets, API keys, tokens, and credentials are removed.
- [ ] Private paths, hostnames, usernames, and repository names are redacted when needed.
- [ ] Customer or employee identifiers are anonymized unless explicitly approved for publication.
- [ ] Logs and screenshots are checked for proprietary code or internal URLs.
- [ ] Claims are limited to the evidence in this case study.

## Publishable summary

Write a short summary that stays inside the evidence.

> QA-Z evaluated `<workflow>` on `<redacted context>`. Before QA-Z, `<measured baseline>`. After running `<commands>`, `<measured result>`. QA-Z did not `<non-goal>`.
