# Case Study Template

QA-Z case studies must be evidence-backed. Do not invent adoption, customer,
usage, performance, or security-impact claims.

Use this template to turn a real or sanitized evaluation into publishable
evidence without leaking private data or overstating what QA-Z proved.

## When To Use This Template

Use this template when documenting a real repository, fixture, or sanitized
evaluation where QA-Z produced deterministic before/after evidence.

Do not use this template to imply that an enterprise, customer, or team uses
QA-Z unless that claim is explicitly approved and sourced.

## Required Sections

### 1. Case Study Summary

- Repository or fixture:
- Scenario:
- Risk:
- QA-Z workflow:
- Status:
- Public claim source:

### 2. Before Evidence

Include the baseline commands, expected failing checks, blocking findings, and
artifact pointers that show the unsafe or unverified starting point.

### 3. After Evidence

Include the candidate commands, verification verdict, and artifact pointers that
show what changed after a human or external executor applied the candidate fix.

### 4. Commands

List exact commands used. If a command was not run, say that instead of filling
the gap with a narrative claim.

### 5. Artifact Pointers

List fast, deep, repair, SARIF, verify, and summary artifacts. Prefer artifact
paths and short sanitized excerpts over committed generated runtime output.

### 6. Validation

Explain how maintainers can reproduce or inspect the evidence. Include local
validation commands, expected verdicts, and any environment assumptions.

### 7. Redaction And Privacy

Explain what was redacted and why. Keep private data out of the published case
study unless disclosure is explicitly approved.

### 8. Non-Goals

Explain what QA-Z did not automate or prove.

### 9. Claims Boundary

State what cannot be claimed without external proof.

## Before/After Evidence Checklist

Before evidence should include:

- baseline run command;
- `.qa-z/runs/<baseline>/fast/summary.json`;
- `.qa-z/runs/<baseline>/deep/summary.json` when deep checks were used;
- `.qa-z/runs/<baseline>/deep/results.sarif` when SARIF was produced;
- `.qa-z/runs/<baseline>/repair/codex.md` or `repair/prompt.md` when repair
  guidance was generated;
- expected failing checks or blocking findings.

After evidence should include:

- candidate run command;
- `.qa-z/runs/<candidate>/fast/summary.json`;
- `.qa-z/runs/<candidate>/deep/summary.json` when deep checks were used;
- `.qa-z/runs/<candidate>/verify/summary.json`;
- `.qa-z/runs/<candidate>/verify/compare.json`;
- `.qa-z/runs/<candidate>/verify/report.md`;
- verification verdict, for example `improved`, `mixed`, `regressed`,
  `unchanged`, or `verification_failed`.

## Command Template

```bash
qa-z fast --output-dir .qa-z/runs/baseline
qa-z deep --from-run .qa-z/runs/baseline
qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex

# Apply or inspect the candidate change outside QA-Z.

qa-z fast --output-dir .qa-z/runs/candidate
qa-z deep --from-run .qa-z/runs/candidate
qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate
```

QA-Z does not apply the repair or decide success with an LLM-only judgment. The
case study should point to deterministic artifacts.

## Artifact Pointers

Use these paths as the default evidence map:

```text
.qa-z/runs/<baseline>/fast/summary.json
.qa-z/runs/<baseline>/deep/summary.json
.qa-z/runs/<baseline>/deep/results.sarif
.qa-z/runs/<baseline>/repair/codex.md
.qa-z/runs/<candidate>/fast/summary.json
.qa-z/runs/<candidate>/deep/summary.json
.qa-z/runs/<candidate>/verify/summary.json
.qa-z/runs/<candidate>/verify/compare.json
.qa-z/runs/<candidate>/verify/report.md
```

If the case study uses GitHub Actions, also point reviewers to the Job Summary
and uploaded `qa-z-runs` artifact instead of copying private run data into the
document.

## Validation

A case study should include the narrowest commands needed to refresh the
published evidence. For docs-only case studies, include the docs checks that
prove the template and public surfaces remain current. For runnable examples,
include the baseline, candidate, and verify commands that generated the
artifact pointers.

Validation should distinguish:

- commands actually run;
- commands that a reviewer can run later;
- commands intentionally skipped;
- expected failing baseline behavior;
- expected candidate or verify verdict.

## Redaction And Privacy

Before publishing a case study, redact:

- secrets, tokens, API keys, credentials;
- private repository names if they are not approved for disclosure;
- private file paths;
- customer names unless explicitly approved;
- user emails and personal data;
- proprietary source snippets that are not required to understand the QA-Z
  evidence;
- internal branch names, ticket IDs, or URLs when they are not needed.

Use sanitized paths such as:

```text
<repo>/src/auth.py
<repo>/.qa-z/runs/baseline/fast/summary.json
```

## Non-Goals

Every case study should state that QA-Z did not:

- edit the target repository;
- apply the repair;
- call live model APIs;
- replace deterministic checks with an LLM-only judgment;
- publish packages;
- create tags or releases;
- deploy;
- create branches, commits, pushes, or GitHub bot comments.

## Claims Boundary

Do not claim:

- a customer uses QA-Z unless the customer explicitly approved the claim;
- adoption counts, user counts, star counts, deployment counts, or revenue impact
  unless they are sourced;
- performance improvements unless measured and linked to evidence;
- security impact beyond what the QA-Z artifacts prove;
- package publishing, release, deployment, or hosted automation unless those
  actions actually occurred.

Prefer wording such as:

- "In this sanitized evaluation..."
- "In this fixture..."
- "QA-Z evidence showed..."
- "The verify verdict was..."

## Generated Artifact Policy

Do not commit generated runtime evidence by default:

- root `.qa-z/**`;
- `benchmarks/results/work/**`;
- `benchmarks/results/summary.json`;
- `benchmarks/results/report.md`;
- `build/**`;
- `dist/**`;
- `.pytest_cache/**`;
- `.mypy_cache/**`;
- `.ruff_cache/**`.

A case study should normally reference artifact paths and include short
sanitized excerpts instead of committing generated outputs. Frozen benchmark
fixture evidence is allowed only when intentionally stored under
`benchmarks/fixtures/**/repo/.qa-z/**` with context.

## Seed Ideas

QA-Z needs concrete adoption stories to move from tool to category leader, but
seed ideas are not customer claims. Turn a seed into a case study only after the
template above is filled with evidence.

### Seed 1: Auth Refactor

An agent simplified authorization. QA-Z caught a non-owner access regression,
produced a repair prompt, and verified the candidate improved.

### Seed 2: Security Scan

An agent introduced a risky flow. Semgrep found it, QA-Z normalized the finding,
and SARIF plus repair prompts gave reviewers a deterministic next step.

### Seed 3: Pull Request Gate

Hypothetical seed: a team installed the QA-Z GitHub Action. PRs with generated
code now preserve fast/deep artifacts before deciding whether the change can
merge.
