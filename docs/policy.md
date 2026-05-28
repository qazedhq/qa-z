# Policy Packs

QA-Z policy packs are local deterministic merge-policy inputs. They name the
rule ids that should block a merge, require review, or map static-analysis
severity to a guard decision. They do not call GitHub, upload packages, post
comments, deploy, or run coding agents.

## Validate A Policy

Use the builtin strict pack when a repository wants a conservative first policy:

```bash
qa-z policy validate --policy strict
```

Machine-readable automation can use:

```bash
qa-z policy validate --policy strict --json
```

The validation payload includes:

- `kind: qa_z.policy_validation`
- `status: valid` or `invalid`
- `policy.name`
- `policy.block_on`
- `policy.require_review`
- `policy.severity_mapping`
- `errors`

## Guard With A Policy

`qa-z guard --policy strict` validates the requested policy before the guard
workflow runs and records the selected policy in the guard verdict JSON.

```bash
qa-z guard --policy strict --adapter codex --deep auto --fail-on-risk
```

The policy selection is evidence metadata in the guard result. It does not
silently mutate the target repository or apply repairs.

## Configured Policy

Repositories can define a local policy in `qa-z.yaml`:

```yaml
merge_policy:
  name: team
  block_on:
    - auth_regression
    - owner_check_removed
    - secret_leak
  require_review:
    - generated_code_change
    - dependency_change
  severity_mapping:
    ERROR: block
    WARNING: review
    INFO: allow
```

`block_on` must contain at least one rule id. `require_review` must be a list,
even when it is empty.

## Boundaries

Policy packs are local deterministic inputs only. They do not grant production
credentials, enable PyPI publishing, create tags, open pull requests, post bot
comments, or contact external services.
