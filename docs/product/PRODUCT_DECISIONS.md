# Product Decisions

## Confirmed Decisions

### QA-Z Is A Codex-First, Model-Agnostic QA Control Plane

- Decision: Build QA-Z as a Codex-first, model-agnostic QA control plane for coding agents.
- Status: confirmed.
- Source: human and repository evidence.
- Rationale: `AGENTS.md`, CONTRIBUTING, release docs, and architecture docs all use this identity.
- Impact on V8: V8 should optimize local QA control-plane evidence, not agent runtime execution.
- Date if available: bootstrap product definition dated 2026-04-11; `AGENTS.md` date not recorded.

### Deterministic Evidence Beats LLM-Only Judgment

- Decision: QA-Z must prefer executable gates, explicit contracts, deterministic evidence, and repairable feedback.
- Status: confirmed.
- Source: human and repository evidence.
- Rationale: This is stated in `AGENTS.md`, README, CONTRIBUTING, SECURITY, and release docs.
- Impact on V8: Do not replace pass/fail checks with LLM-only scoring or subjective review language.
- Date if available: not recorded.

### Preserve Core Command Names

- Decision: Preserve `init`, `plan`, `fast`, `deep`, `review`, and `repair-prompt`.
- Status: confirmed.
- Source: human.
- Rationale: `AGENTS.md` calls these core command names out directly.
- Impact on V8: Treat these commands as public product API. Do not rename, remove, or radically change them without explicit approval.
- Date if available: not recorded.

### Codex And Claude Are Adapters

- Decision: Codex and Claude integrations are adapter/handoff surfaces, not the core engine.
- Status: confirmed.
- Source: human and repository evidence.
- Rationale: `AGENTS.md`, architecture docs, and repair handoff docs all keep agent-specific behavior outside the core planner.
- Impact on V8: Keep vendor-specific prompts/templates in adapters, templates, or bridge outputs.
- Date if available: not recorded.

### Deep Automation Must Be Proved

- Decision: Do not claim deep QA automation exists unless runners and tests prove it.
- Status: confirmed.
- Source: human and repository evidence.
- Rationale: `AGENTS.md` states this directly; current docs describe Semgrep-backed deep checks and SARIF rather than generic AI deep review.
- Impact on V8: Scope deep-readiness work to implemented engines and tested behavior.
- Date if available: not recorded.

### QA-Z Does Not Run Live Agents Or Edit Code

- Decision: QA-Z produces contracts, evidence, prompts, bridge packages, and verification artifacts; it does not call live agents or edit code itself.
- Status: confirmed.
- Source: repository evidence.
- Rationale: README, release docs, repair-session docs, CI comments, and safety docs state this boundary.
- Impact on V8: Do not introduce live model execution, autonomous editing, or remote orchestration in production-readiness loops.
- Date if available: release docs for `v0.9.8-alpha`.

### Generated Runtime Artifacts Stay Local By Default

- Decision: Root `.qa-z/**`, benchmark result outputs, build artifacts, and caches should remain local unless intentionally frozen with context.
- Status: confirmed.
- Source: repository evidence.
- Rationale: README, generated-vs-frozen evidence policy, release handoff, and PR template all enforce this.
- Impact on V8: Do not stage generated artifacts as proof; use them as local evidence and summarize relevant results.
- Date if available: release docs for `v0.9.8-alpha`.

### Public Docs Must Match Implementation State

- Decision: Keep README, examples, config, and docs aligned with actual behavior.
- Status: confirmed.
- Source: human and repository evidence.
- Rationale: `AGENTS.md` requires README alignment, and current-truth docs/tests protect public docs.
- Impact on V8: If V8 changes CLI behavior, it must update tests and public examples; for docs-only work, it must not overclaim current behavior.
- Date if available: not recorded.

## Inferred Decisions

### Primary User Is The Agent-Using Developer Or Reviewer

- Inference: The primary user is a developer, maintainer, or reviewer who uses coding agents and needs merge-readiness evidence.
- Evidence: README asks whether a change is safe to merge; docs focus on local repositories, PRs, CI, and repair prompts.
- Confidence: high.
- Impact on V8: Prioritize merge-readiness flows and repair evidence over broad product-management features.
- Should human confirm? yes.

### CLI/Artifact-First Is The Current Product Form

- Inference: QA-Z should remain CLI/artifact-first for the current production-readiness work.
- Evidence: Current implementation is a Python CLI; docs describe local artifacts as the observability layer; no UI exists.
- Confidence: high for current state, medium for long-term target.
- Impact on V8: Improve CLI output, artifacts, docs, and CI integration before proposing UI/dashboard work.
- Should human confirm? yes for long-term product form.

### Verification Is Product-Critical

- Inference: `verify` and repair-session verification are as product-critical as fast/deep gates because they determine whether repair actually improved evidence.
- Evidence: README core workflow includes `verify`; artifact schema and repair-session docs define improved/mixed/regressed verdicts; tests and benchmark fixtures cover verification.
- Confidence: high.
- Impact on V8: Prioritize tests and docs around baseline/candidate comparison before expanding executor workflows.
- Should human confirm? no, unless product scope changes.

### Benchmark Corpus Is A Production-Readiness Gate

- Inference: `qa-z benchmark --json` is a product readiness gate, not only a developer convenience.
- Evidence: release docs cite benchmark pass rates; CONTRIBUTING requires benchmark for CLI/artifact/workflow/benchmark/public-doc changes.
- Confidence: high.
- Impact on V8: Use benchmark fixtures to prove behavior across representative product contracts.
- Should human confirm? no.

### Self-Improvement Loops Are Planning Loops, Not Editing Loops

- Inference: `self-inspect`, `select-next`, `backlog`, and `autonomy` are intended to choose evidence-backed work while keeping actual edits outside QA-Z.
- Evidence: README and docs state autonomy does not edit source, call agents, or run queues.
- Confidence: high.
- Impact on V8: V8 can use these artifacts as guidance but must still apply human/Codex judgment and deterministic validation.
- Should human confirm? no.

## Deferred Decisions

### Hosted Or Team Product Direction

- Decision needed: Should QA-Z become a hosted/team product or remain local CLI/open-source tooling?
- Why it matters: Hosted scope changes security, data retention, auth, permissions, observability, and buyer workflows.
- Options: local-only; local CLI plus optional cloud dashboard; fully hosted service.
- Recommended default: local-only until explicitly confirmed.
- Risk if unresolved: V8 may overbuild UI, accounts, billing, or remote orchestration.

### Write-Enabled GitHub Integrations

- Decision needed: Should QA-Z ever post PR comments, write Checks API results, mutate branches, or update PRs?
- Why it matters: Current safety boundary is read/artifact oriented.
- Options: no write integrations; opt-in annotation helper; bot comments; full Checks integration.
- Recommended default: no write integrations.
- Risk if unresolved: V8 may introduce permissions and side effects outside confirmed scope.

### Deep Engine Roadmap

- Decision needed: Which deep engines are production requirements beyond Semgrep?
- Why it matters: The product goal mentions deep QA, but current evidence is Semgrep-centered.
- Options: Semgrep only for alpha; add CodeQL; add Trivy; add property/smoke/mutation engines; plugin model.
- Recommended default: strengthen Semgrep and SARIF first, then add one deterministic engine at a time.
- Risk if unresolved: V8 may add shallow integrations without benchmark proof.

### Artifact Redaction And Retention

- Decision needed: What should QA-Z redact from stdout/stderr tails and how long should local artifacts be retained?
- Why it matters: Artifacts are valuable evidence but can contain sensitive paths or secret-like output.
- Options: no redaction beyond user caution; secret-pattern redaction; configurable retention; explicit cleanup command.
- Recommended default: document current behavior and avoid uploading sensitive artifacts.
- Risk if unresolved: security/privacy posture remains incomplete for production teams.

### Package Publishing And Release Cadence

- Decision needed: Should production readiness include PyPI/TestPyPI publish, signed tags, cadence, and support policy?
- Why it matters: Release docs show GitHub prerelease but no package registry publish.
- Options: GitHub-only prerelease; TestPyPI; PyPI alpha; stable semver release cadence.
- Recommended default: keep GitHub alpha until package publishing approval.
- Risk if unresolved: V8 may call release "production" without distribution readiness.

### Executor Bridge Product Tier

- Decision needed: Is executor bridge/result ingest a core user workflow or advanced operator workflow?
- Why it matters: It affects docs hierarchy, validation budget, and UX polish priorities.
- Options: advanced only; core repair workflow; hidden/internal safety layer.
- Recommended default: advanced workflow until external-executor usage is confirmed.
- Risk if unresolved: V8 may overprioritize bridge UX over primary merge-readiness flows.

### Production Success Metrics

- Decision needed: Which product metric defines production success?
- Why it matters: V8 needs a North Star for improvement loops.
- Options: completed evidence bundles per agent change; verified repair rate; benchmark pass rate; CI adoption; time-to-review.
- Recommended default: complete deterministic merge-readiness evidence bundle rate.
- Risk if unresolved: V8 may optimize local code quality metrics without product impact.

## Explicit Non-Goals

### Live Model Execution

- Non-goal: QA-Z does not call live Codex, Claude, or other model APIs.
- Source: README, release docs, repair-session docs, CI comments.
- Why it matters: Keeps local flows deterministic and model-agnostic.
- What V8 should avoid: API clients, secrets, remote executor calls, hidden network behavior.

### Autonomous Code Editing

- Non-goal: QA-Z does not edit source code by itself.
- Source: README, release docs, repair-session docs.
- Why it matters: QA-Z is the QA layer around repair, not the repair agent.
- What V8 should avoid: applying patches from QA-Z runtime commands or making autonomy loops mutate source.

### Remote Orchestration

- Non-goal: No remote queues, schedulers, daemons, or workers.
- Source: README, release docs, repair-session docs.
- Why it matters: Current product is local CLI and artifacts.
- What V8 should avoid: background services, queue state, cloud worker assumptions.

### Automatic Git Mutation

- Non-goal: QA-Z does not create branches, commits, pushes, deployments, or bot comments.
- Source: README, release docs, CI comments.
- Why it matters: Maintainers own repository mutation.
- What V8 should avoid: commands or docs implying QA-Z will mutate GitHub or Git state.

### LLM-Only Pass/Fail Authority

- Non-goal: LLM-only judgment cannot replace deterministic checks.
- Source: AGENTS, CONTRIBUTING, SECURITY.
- Why it matters: The product promise is executable evidence.
- What V8 should avoid: severity reclassification or merge verdicts based only on model text.

### Hidden Network Dependencies

- Non-goal: Local QA flows should not add hidden network dependencies.
- Source: AGENTS and CONTRIBUTING.
- Why it matters: Local/CI reproducibility and security depend on explicit tools.
- What V8 should avoid: auto-installing tools, calling package indexes or remote APIs without docs and approval.

### Billing, Accounts, Team Administration

- Non-goal: Billing, accounts, and team administration are not part of confirmed MVP or alpha scope.
- Source: absence from repository plus current local CLI positioning.
- Why it matters: These would change product category and architecture.
- What V8 should avoid: adding commercial/product-management surfaces without human decision.

## Open Product Questions

### Target User

- Who is the named primary persona: solo developer, team reviewer, QA engineer, or platform owner?
- Should non-developer QA/security roles be first-class in docs and workflows?
- What repository sizes and team sizes should production QA-Z support?

### Core Workflow

- Is `doctor` part of the canonical workflow or an operator-only health check?
- Is `verify` mandatory before merge in the target production workflow?
- Should repair-session/executor-bridge appear in quickstart or advanced docs?
- What is the minimum evidence bundle for a "safe to merge" recommendation?

### Business Logic

- Which checks are blocking by default for Python and TypeScript profiles?
- How should QA-Z classify scan-quality warnings with no blocking findings?
- Should missing tests be warn or fail by default in production profiles?
- What policy should govern repeated unchanged or no-op repair attempts?

### Data Model

- Which artifact schemas are stable public API?
- Should artifact schema versions have migration docs?
- How should local artifact retention and cleanup be configured?
- Should benchmark fixture expected contracts be versioned independently?

### Security/Privacy

- Should stdout/stderr tails be redacted before writing artifacts?
- Should SARIF and GitHub summaries omit potentially sensitive paths or snippets?
- What secret-handling policy should examples and tests enforce?
- What permissions are acceptable in CI templates beyond `contents: read` and optional `security-events: write`?

### Integrations

- Which CI providers are officially supported beyond GitHub Actions?
- Which deep engines should be added after Semgrep?
- Should QA-Z support JUnit, annotations, or Checks API output?
- Should external executor bridge packages have a formal stable contract for third-party tools?

### UX

- Should CLI output optimize for human readability, copy/paste repair commands, or machine parsing?
- Should every failure emit a concrete next command?
- How much context should adapter prompts include before becoming too noisy?
- Should docs include a single "golden path" from first install to verified repair?

### Operations

- What is the production release cadence?
- Should `v1.0` require package registry publication?
- What remote preflight evidence must be current before release?
- How should Windows-specific tool quirks be documented for operators?

### Metrics

- What North Star metric should V8 optimize?
- What benchmark pass rate is required for release?
- What maximum runtime is acceptable for fast, deep, benchmark, and release gates?
- What rate of repair prompts leading to improved verification should be targeted?
