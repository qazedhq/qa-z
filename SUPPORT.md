# Support

QA-Z is an alpha developer tool. Please route requests by risk and urgency so
maintainers can keep deterministic evidence ahead of claims.

## Where To Ask

- Bug reports: open a GitHub issue with the exact command, exit code, and
  relevant `.qa-z/` artifact path. Do not include live secrets.
- Security issues: follow [SECURITY.md](SECURITY.md) and prefer a private
  GitHub Security Advisory.
- Usage questions: open a GitHub issue with the `question` label or use the
  docs linked from [docs/README.md](docs/README.md).
- Release, package, tag, or deploy approvals: use the release handoff packet;
  these actions require explicit human approval and are never inferred from
  local green checks.

## Before Opening An Issue

Run the smallest command that reproduces the problem:

```bash
python -m qa_z doctor --json
python -m qa_z --help
```

If the report involves merge-safety evidence, include the command that produced
the run directory and the path under `.qa-z/runs/`. If the report involves a
public alpha release, include the relevant release note or handoff document.

## Current Limits

QA-Z does not edit target repositories, call live model APIs, push branches,
publish packages, deploy services, or post GitHub comments by itself. Requests
for those actions need a separate approved release or integration plan.
