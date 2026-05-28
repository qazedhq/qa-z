# Governance

QA-Z governance commands create local deterministic artifacts for teams that
need baseline, waiver, and audit-trail evidence before merge. They are local
files under `.qa-z/governance/`; they do not contact GitHub, publish packages,
deploy, or repair target repositories.

## Baseline

Create a local governance baseline:

```bash
qa-z baseline create --json
```

This writes:

```text
.qa-z/governance/baseline.json
```

The baseline records whether `qa-z.yaml` exists, whether a latest run exists,
and whether a waiver store already exists.

## Waivers

Add an expiring waiver:

```bash
qa-z waiver add \
  --finding-id AUTH-001 \
  --owner security \
  --reason "False positive after manual review." \
  --expires 2099-12-31 \
  --json
```

This appends to:

```text
.qa-z/governance/waivers.json
```

Waivers require a finding id, owner, reason, and `YYYY-MM-DD` expiration. The
command records `active` or `expired` from the expiration date.

## Report

Summarize local governance state:

```bash
qa-z governance report --json
```

The report includes baseline status, active/expired waiver counts, and the local
audit trail paths.

## Boundaries

Governance artifacts are local deterministic evidence. They are not approval to
merge, publish, deploy, tag, upload to PyPI, or run an external executor.
