# Product Direction

## Status

Status: Partially confirmed.

The product identity, core direction, guardrails, and command spine are human-confirmed in `AGENTS.md` and reinforced by the bootstrap product definition brief. The current implementation state is evidence-backed by the README, architecture docs, release notes, CLI registry, config, CI workflows, and tests. Target users, buyer profile, success metrics, and some production-grade scope are inferred and still need product review.

Input reconciliation note: no separate file literally named "A1 Product Definition Brief" was found in this checkout. This document treats `docs/superpowers/specs/2026-04-11-qa-z-bootstrap-design.md` as the repository product definition brief because it contains the original "Product Definition" section and public bootstrap intent.

## Product Summary

- Product name: QA-Z.
- Product category: local QA control plane for coding-agent workflows.
- One-sentence description: This product is a local QA control plane for developers and coding-agent operators that helps them decide whether agent-produced code is safe to merge by turning change context into executable contracts, deterministic checks, local artifacts, review packets, repair prompts, and post-repair verification evidence.
- Current maturity: alpha, with package metadata at `0.9.8a0` and release docs for `v0.9.8-alpha`.
- Confidence level: high for identity and current capabilities; medium for target user and production metrics; low for hosted/commercial packaging.

## Confirmed Product Direction

### Confirmed Decisions

- Confirmed: QA-Z is Codex-first but model-agnostic. Codex and Claude are adapters or handoff targets, not the core engine.
- Confirmed: QA-Z should bias toward executable quality gates, explicit contracts, deterministic evidence, and repairable feedback.
- Confirmed: The core command names `init`, `plan`, `fast`, `deep`, `review`, and `repair-prompt` must be preserved.
- Confirmed: Deep QA automation must not be claimed unless runners and tests prove it.
- Confirmed: Local QA flows must not hide network dependencies.
- Confirmed: Deterministic pass/fail checks must not be replaced by LLM-only judgment.
- Confirmed: Agent-specific logic belongs in `adapters/`, templates, prompts, or bridge surfaces, not the core planner.

### Confirmed Constraints

- Current state: QA-Z does not edit code by itself.
- Current state: QA-Z writes local `.qa-z/**` artifacts and keeps root runtime evidence local by default.
- Current state: QA-Z provides repair handoff material for external tools and humans instead of calling live model APIs.
- Current state: CI and release workflows preserve fast/deep evidence before applying final verdicts.
- Confirmed: Public docs and README must stay aligned with actual implementation state.

### Confirmed Non-Goals

- No live Codex, Claude, or other model execution in local QA flows.
- No autonomous code editing.
- No remote orchestration, queues, schedulers, or daemons.
- No automatic branch mutation, commits, pushes, deployments, or GitHub bot comments from QA-Z itself.
- No LLM-only judge replacing deterministic pass/fail gates.
- No hidden network dependencies in local QA flows.

### Open Questions

- Requires human decision: Is QA-Z primarily an open-source CLI product, a future hosted service, or both?
- Requires human decision: Should production scope include a persistent UI or remain CLI/artifact-first?
- Requires human decision: Which languages and deep engines are required before calling the product production-grade?
- Requires human decision: What level of GitHub integration is acceptable beyond summaries, SARIF, and workflow artifacts?
- Requires human decision: What monetization, team administration, or buyer workflow exists, if any?

## Target Users

- Primary users: developers, code reviewers, and repository maintainers who use AI coding agents and need deterministic merge-readiness evidence.
- Secondary users: CI maintainers, QA engineers, security reviewers, and team leads who need review packets, SARIF, benchmark evidence, or release gates.
- Admin/operator users: release operators and local repo owners who configure `qa-z.yaml`, run validation gates, manage generated artifacts, and decide whether to accept or reject repair results.
- Buyer/customer: unclear. Inferred candidates are engineering teams adopting coding agents and open-source maintainers who need agent-safe QA workflows.
- User roles found in the repository: human operator, external repair executor, Codex adapter, Claude adapter, GitHub Actions job, reviewer, maintainer, benchmark fixture author, release operator.
- Unknowns: exact buyer, team size, hosted versus local deployment, enterprise policy requirements, and whether non-developer QA roles are first-class users.

## Core Problem

### Repository Evidence

The README states that AI coding agents can write code fast and that QA-Z helps decide whether that code is safe to merge. The product turns code changes into QA contracts, deterministic checks, review packets, repair prompts, verification evidence, GitHub summaries, SARIF, and benchmark artifacts. The architecture document describes QA-Z as a local, model-agnostic QA control plane that turns code-review context into deterministic contracts, checks, artifacts, and repair handoff material.

### Inference

The painful workflow is the gap between "an agent changed code" and "a maintainer can trust the change." Without QA-Z, humans must manually derive acceptance criteria, remember which checks matter, inspect raw failure dumps, produce repair instructions, and determine whether a second agent pass improved or regressed the repository. QA-Z exists to make that loop explicit, repeatable, and evidence-backed.

### Expected User Outcome

A user can point QA-Z at a repository change, produce a QA contract, run deterministic gates, inspect a review packet, hand a focused repair prompt to a human or external agent, and verify whether the repair improved the evidence before merge.

## Value Proposition

- Main value proposition: QA-Z gives coding-agent users a deterministic QA layer around agent-generated code so merge decisions are based on contracts, executable checks, artifacts, and repairable guidance rather than informal confidence.
- Differentiators: local-first operation, model-agnostic core, explicit artifact contracts, repair-prompt generation, post-repair verification, benchmark fixtures, and strict non-goals around live model execution.
- User success: fewer unsafe or unverified agent changes reach merge, and failed changes produce clear next repair actions.
- Product success: QA-Z becomes the trusted local control plane that teams run before accepting coding-agent output.

## MVP Product Goal

- MVP target user: a developer or maintainer using Codex, Claude, or another coding agent in a Python repository.
- MVP core workflow: `init -> plan -> fast -> review --from-run -> repair-prompt`.
- MVP must-have features:
  - create starter config and contract workspace with `init`;
  - generate QA contract drafts from issue/spec/diff context with `plan`;
  - run deterministic fast checks with `fast`;
  - render review packets from run artifacts with `review`;
  - render repair prompts and handoff artifacts with `repair-prompt`;
  - write JSON and Markdown artifacts locally;
  - document placeholders honestly.
- MVP must-not-have scope:
  - live agent APIs;
  - autonomous code editing;
  - remote orchestration;
  - speculative deep automation;
  - automatic commit/push/comment behavior.
- MVP success criteria:
  - install from source;
  - `python -m pytest` passes;
  - `python -m qa_z init` creates starter config and contracts workspace;
  - a runnable Python example demonstrates the local flow;
  - README accurately states what is implemented and what is not.
- MVP risks:
  - overclaiming deep automation;
  - config and README drifting from command behavior;
  - generated artifacts being mistaken for source;
  - repair prompts becoming vague instead of evidence-backed.

## Production Product Goal

The production goal is to deliver a reliable local QA control plane for developers, code reviewers, and coding-agent operators that lets them decide whether agent-produced code is safe to merge through contract generation, deterministic fast/deep gates, artifact-backed review, repair handoff, post-repair verification, CI summaries, SARIF, benchmark coverage, and local self-improvement planning, with production-grade security, reliability, testing, deployment, observability through artifacts, data integrity, documentation, and maintainability appropriate for local repositories and CI pipelines.

- Production target user: teams and maintainers who rely on AI coding agents for recurring repository changes and need enforceable merge-readiness evidence.
- Production core workflows:
  - repository onboarding and config validation;
  - contract generation from issue/spec/diff context;
  - deterministic fast and deep gates;
  - review packet and GitHub summary rendering;
  - repair prompt and repair-session packaging;
  - executor bridge/result ingest for external repair tools;
  - baseline-versus-candidate verification;
  - benchmark and self-inspection loops;
  - release/readiness gate execution.
- Production must-have capabilities:
  - stable artifact schemas with backward compatibility;
  - deterministic check execution and failure preservation;
  - Semgrep-backed deep evidence and SARIF output;
  - model-agnostic adapters and handoff surfaces;
  - generated-artifact policy and cleanup guidance;
  - benchmark corpus covering fast, deep, repair, verification, bridge, executor-result, and safety cases;
  - CI workflows that preserve evidence and fail based on recorded exits;
  - clear docs for current state, limits, and production-readiness gates.
- Production quality bar:
  - validation commands are documented and reproducible;
  - failure modes produce artifacts and next actions;
  - local runtime artifacts stay local unless intentionally frozen;
  - config, README, tests, examples, and release docs stay in current-truth sync;
  - no unplanned network, live executor, branch, commit, push, or bot-comment behavior.
- Production success criteria:
  - core CLI flows are stable across supported platforms;
  - release gate and benchmark corpus are green for the baseline;
  - critical artifact schemas are tested;
  - failure and repair loops are understandable without reading source;
  - users can safely integrate QA-Z into CI without granting write permissions.
- Production non-goals:
  - becoming a coding agent;
  - becoming a hosted queue or scheduler without explicit product approval;
  - replacing code review with LLM-only evaluation;
  - silently installing or calling external tools beyond documented commands.
- Production risks:
  - expanding into orchestration before local evidence contracts are stable;
  - conflating generated evidence with source;
  - adding agent-specific behavior to core modules;
  - broadening language/deep-engine support faster than tests and benchmarks can prove.

## Core Workflows

### Repository Onboarding

- User goal: initialize QA-Z in a repository with explicit config and optional templates.
- Entry point: `python -m qa_z init`.
- Main steps: choose profile/options, write `qa-z.yaml`, create `qa/contracts`, optionally add agent templates and GitHub workflow.
- Expected result: starter workspace is ready for local QA-Z gates.
- Current repository evidence: README quickstart, CLI help, `src/qa_z/commands/bootstrap*.py`, tests for init options and bootstrap commands.
- Production criticality: high, because onboarding is activation.
- Test/E2E status if known: covered by CLI/bootstrap tests; broader installed-package smoke exists in release tooling.

### Contract Planning

- User goal: convert issue/spec/diff context into an explicit QA contract.
- Entry point: `python -m qa_z plan`.
- Main steps: provide title and context files, generate contract sections, store under configured `contracts.output_dir`.
- Expected result: a contract with scope, assumptions, invariants, risk edges, negative cases, and acceptance checks.
- Current repository evidence: `qa-z.yaml.example`, docs MVP issues, planner modules, planning command tests.
- Production criticality: high, because checks and repair prompts need explicit intent.
- Test/E2E status if known: command and contract-resolution tests exist; quality of generated contract content remains an ongoing product area.

### Fast Gate

- User goal: run deterministic lint, format, type, and test checks.
- Entry point: `python -m qa_z fast`.
- Main steps: load config, resolve selection mode, execute configured checks, write `fast/summary.json`, per-check artifacts, and summary Markdown.
- Expected result: pass/fail evidence with stdout/stderr tails and selected checks.
- Current repository evidence: README, `qa-z.yaml.example`, `src/qa_z/runners/fast.py`, artifact schema docs, fast selection tests.
- Production criticality: very high, because fast checks are the primary merge gate.
- Test/E2E status if known: covered by many fast/config/selection tests and CI.

### Deep Gate

- User goal: run deeper risk-oriented checks, currently Semgrep-backed, and preserve findings.
- Entry point: `python -m qa_z deep`.
- Main steps: resolve run attachment, execute configured deep checks, normalize Semgrep JSON, apply suppression/threshold policy, write deep summary and SARIF.
- Expected result: blocking and non-blocking deep evidence with scan-quality diagnostics.
- Current repository evidence: README, architecture docs, artifact schema docs, `src/qa_z/runners/deep.py`, `src/qa_z/runners/semgrep.py`, SARIF reporter, deep/Semgrep tests.
- Production criticality: high for security/risk coverage, but must remain honest about current Semgrep-centered scope.
- Test/E2E status if known: covered by deep, Semgrep normalization, SARIF, benchmark, and CI workflow surfaces.

### Review Packet

- User goal: turn run artifacts into a concise review packet for merge decision-making.
- Entry point: `python -m qa_z review --from-run latest`.
- Main steps: load run artifacts, render contract context, executed checks, failures, and recommendations.
- Expected result: Markdown and JSON review evidence.
- Current repository evidence: README, reporter modules, review packet tests, GitHub workflow summary generation.
- Production criticality: high, because it is the human review surface.
- Test/E2E status if known: review command and reporter tests exist.

### Repair Prompt And Handoff

- User goal: create an evidence-backed repair prompt for Codex, Claude, a human, or another executor.
- Entry point: `python -m qa_z repair-prompt --from-run latest --adapter codex`.
- Main steps: load failed fast/deep evidence, select repair targets, write packet, prompt, handoff JSON, and adapter Markdown.
- Expected result: repairable instructions with affected files, non-goals, and validation commands.
- Current repository evidence: artifact schema docs, repair handoff modules, repair prompt tests, adapter docs.
- Production criticality: high, because raw failures need repairable feedback.
- Test/E2E status if known: repair prompt and handoff tests exist.

### Post-Repair Verification

- User goal: prove whether a candidate repair improved, regressed, mixed, or stayed unchanged versus baseline evidence.
- Entry point: `python -m qa_z verify --baseline-run <run> --candidate-run <run>` or repair-session verification.
- Main steps: load baseline/candidate summaries, compare fast checks and deep findings, write verify artifacts and report.
- Expected result: deterministic verdict with resolved, remaining, new, and regressed issue counts.
- Current repository evidence: README, artifact schema docs, verification modules, verification tests.
- Production criticality: very high, because it protects against false repair claims.
- Test/E2E status if known: verification comparison tests and benchmark fixtures exist.

### Repair Session And Executor Bridge

- User goal: package a local repair workflow and optionally hand it to an external executor without live orchestration.
- Entry point: `qa-z repair-session`, `qa-z executor-bridge`, `qa-z executor-result`.
- Main steps: create session from baseline run, package safety and handoff inputs, ingest returned executor result, run deterministic verification when appropriate.
- Expected result: local session artifacts, bridge package, result ingest report, and next recommendation.
- Current repository evidence: repair sessions docs, pre-live executor safety docs, executor bridge/result modules and tests.
- Production criticality: high for future external-executor workflows, but must stay live-free until approved.
- Test/E2E status if known: substantial executor bridge/result and dry-run tests exist.

### Benchmark And Self-Improvement Planning

- User goal: measure QA-Z behavior and choose improvement work from deterministic evidence.
- Entry point: `qa-z benchmark`, `qa-z self-inspect`, `qa-z select-next`, `qa-z backlog`, `qa-z autonomy`.
- Main steps: run seeded benchmark fixtures or inspect artifacts, update backlog, select evidence-backed tasks, prepare local planning loops.
- Expected result: benchmark summary/report, improvement backlog, selected tasks, and loop plan artifacts.
- Current repository evidence: benchmarking docs, autonomy/self-improvement modules, benchmark fixtures, tests.
- Production criticality: medium-high for product hardening; lower than primary user merge gates.
- Test/E2E status if known: benchmark and self-improvement tests exist; generated benchmark results stay local by default.

## Current Capabilities

| Capability | Current status | Evidence | Production relevance |
| --- | --- | --- | --- |
| CLI command spine | implemented, tested | README, CLI help, command registry, tests | Core public API |
| Config and doctor validation | implemented, tested | `qa-z.yaml.example`, `qa_z doctor --help`, config validation tests | Onboarding and safe local use |
| Contract generation | implemented, tested | planner modules, README, planning tests | Intent capture |
| Python fast checks | implemented, tested | `qa-z.yaml`, fast runner, CI, fast tests | Primary local gate |
| TypeScript fast checks | implemented in example/config and benchmark coverage | `qa-z.yaml.example`, examples, benchmarks | Mixed-repo support |
| Semgrep deep checks | implemented, tested | deep runner, Semgrep docs/tests, CI workflow | Security/risk gate |
| SARIF output | implemented, tested | artifact schema, SARIF reporter/tests, CI upload step | GitHub code scanning integration |
| Review packet rendering | implemented, tested | reporters and review tests | Human review surface |
| Repair prompt/handoff | implemented, tested | artifact schema, repair handoff tests | Repairable feedback |
| Repair sessions | implemented, tested | docs, session modules/tests | Local repair workflow wrapper |
| Verify baseline/candidate | implemented, tested | verification modules/tests | Anti-regression proof |
| Executor bridge and result ingest | implemented, tested | repair sessions docs, executor tests | External executor boundary |
| Benchmark corpus | implemented, tested | benchmark docs, fixtures, release evidence | Product regression measurement |
| Self-inspection/autonomy planning | implemented, tested | autonomy docs/source/tests | Internal improvement loop |
| Live agent execution | not implemented, non-goal | README, release docs, safety docs | Must not be introduced without approval |
| Remote orchestration | not implemented, non-goal | README, repair docs, release docs | Must not be introduced without approval |
| Hosted UI or service | unclear / not present | no repository evidence | Requires human product decision |

## Domain Model

- Core entities:
  - Project: repository under QA-Z inspection.
  - Config: `qa-z.yaml` or `qa-z.yaml.example`.
  - Contract: QA intent document under `qa/contracts`.
  - Run: local fast/deep evidence directory under `.qa-z/runs`.
  - Check: configured deterministic command such as lint, format, type, test, or Semgrep.
  - Finding: normalized deep issue, usually from Semgrep.
  - Review packet: rendered summary from run artifacts.
  - Repair packet/handoff: executor-facing repair contract and adapter Markdown.
  - Repair session: local workflow wrapper around baseline evidence and candidate verification.
  - Executor bridge: packaged input bundle for an external executor.
  - Executor result: returned evidence from an external repair attempt.
  - Verification comparison: baseline/candidate verdict artifacts.
  - Benchmark fixture/result: seeded contract for measuring QA-Z behavior.
  - Backlog item and autonomy loop: evidence-backed product-improvement planning records.
- Relationships:
  - Project owns config, contracts, and local `.qa-z` artifacts.
  - Runs may contain fast and deep summaries.
  - Review and repair artifacts derive from existing runs.
  - Repair sessions reference a baseline run and produce or compare candidate evidence.
  - Executor bridge packages repair-session context; executor-result ingest validates returned evidence before verification.
  - Benchmarks execute or compare fixture repositories against expected contracts.
- Ownership model:
  - Human operator owns repository changes, merge decisions, generated-artifact staging, and product approvals.
  - QA-Z owns deterministic artifact generation and validation.
  - External executors own code edits outside QA-Z.
  - CI owns repeatable gate execution and artifact upload.
- Roles/permissions:
  - Local operator can run CLI and manage artifacts.
  - CI uses read permissions plus security-events for SARIF upload.
  - QA-Z should not require write permissions for commits, PR comments, branches, or deployments.
- Important states:
  - Run status: passed, failed, error, unsupported.
  - Verification verdict: improved, unchanged, mixed, regressed, verification_failed.
  - Repair session states: created, handoff_ready, waiting_for_external_repair, candidate_generated, verification_complete, completed, failed.
  - Executor result statuses: completed, partial, failed, no_op, not_applicable, rejected or warning states through ingest.
  - Autonomy outcomes: selected, fallback_selected, blocked_no_candidates.
- Business rules confirmed:
  - Deterministic checks are authoritative over LLM-only judgment.
  - Root `.qa-z/**` is local by default.
  - Fixture-local `.qa-z/**` can be tracked only as benchmark input.
  - Codex and Claude behavior belongs in adapters/templates/handoff docs.
  - Deep automation claims must match proven runner/test behavior.
- Business rules inferred:
  - The merge decision should be blocked by failed fast/deep gates until repair evidence improves.
  - Review packets and repair prompts should be generated from artifacts, not from live repo guessing.
  - Benchmark fixtures should be small, intentional product regression contracts.
- Missing or unclear rules:
  - Production support policy and versioning beyond alpha.
  - Commercial/team permission model.
  - How multiple repositories or organizations would be managed if a service is introduced.
  - Which non-Semgrep deep engines are required.

## Product Scope

### In Scope

- Local CLI-first QA control plane.
- Config-driven fast and deep gates.
- Artifact schemas and deterministic summaries.
- Review packets, repair prompts, and adapter Markdown.
- Repair-session packaging, executor bridge, executor-result ingest, and verification.
- Benchmark corpus and self-improvement planning.
- GitHub Actions summaries, SARIF upload, and artifact preservation.
- Documentation that states current implementation honestly.

### Out Of Scope

- Live model API calls.
- Autonomous source editing by QA-Z.
- Remote workers, queues, schedulers, hosted orchestration, and daemons.
- Automatic commits, branches, pushes, deployments, PR comments, or Checks API mutations.
- Billing, account management, and team administration.
- Broad UI redesign or dashboard work without confirmation.

### Non-Goals

- QA-Z is not a coding agent.
- QA-Z is not an LLM-only review judge.
- QA-Z is not a replacement for human merge ownership.
- QA-Z is not a hidden dependency installer.

### Future Opportunities

- Broader TypeScript deep QA.
- Additional deep engines such as CodeQL, Trivy, property tests, mutation tests, or smoke-test engines after deterministic contracts exist.
- Richer GitHub annotations after local publishing contracts are stable.
- Better mixed-language benchmark realism.
- Hosted or team workflows only after human confirmation.

## North Star And Metrics

- Suggested North Star metric: percentage of agent-produced changes that reach a deterministic merge recommendation with complete contract, fast/deep, review, repair, and verification evidence.
- Supporting product metrics:
  - time from change context to review packet;
  - percentage of failed runs with actionable repair targets;
  - percentage of repair attempts classified by `verify`;
  - benchmark fixture pass rate;
  - number of supported language/check surfaces with deterministic tests.
- Engineering quality metrics:
  - `python -m pytest` pass rate;
  - Ruff, mypy, and release gate pass rate;
  - artifact schema compatibility coverage;
  - docs/current-truth guard coverage;
  - benchmark corpus pass rate.
- Reliability metrics:
  - rate of missing-tool errors with useful guidance;
  - rate of generated-artifact policy violations;
  - rate of stale or mismatched executor-result rejection;
  - CI artifact upload and SARIF availability.
- Metrics requiring confirmation:
  - adoption/activation target;
  - acceptable false-positive and false-negative rates;
  - production SLA, if any;
  - team or enterprise reporting metrics.

## Production Readiness Priorities

- Critical flow reliability: protect `init -> plan -> fast -> deep -> review -> repair-prompt -> verify`.
- Security and privacy: keep local flows free of hidden network calls and do not expose secrets in artifacts.
- Data integrity: preserve artifact schema compatibility and generated-artifact policy boundaries.
- API/CLI contract stability: preserve command names and artifact paths.
- E2E and benchmark coverage: keep CLI flows and benchmark fixtures representative.
- UX error states: missing tools, invalid config, stale artifacts, Semgrep failures, and executor-result mismatch should produce actionable guidance.
- Observability: artifacts, summaries, gate JSON, SARIF, and CI job summaries are the observability layer.
- Deployment/readiness: release gate, package build, artifact smoke, preflight, and CI must stay reproducible.
- Documentation accuracy: README, docs index, release notes, `qa-z.yaml.example`, and current-truth docs must match implementation.

## Open Questions

### Product Scope

- Should QA-Z remain local-first only, or become a hosted/team product later?
- Which alpha features are required before the next public beta?
- Should `doctor` become part of the canonical public workflow?

### Target User

- Is the primary persona an individual maintainer, a team reviewer, a QA engineer, or an engineering platform owner?
- Are non-Python/TypeScript teams first-class near-term users?

### Core Workflows

- Which workflow is the activation moment for new users: `init`, first passing `fast`, first repair prompt, or first verified repair?
- Should repair-session and executor-bridge be presented as advanced workflows or core production workflows?

### Business Logic

- What policies decide when a failure blocks merge versus warns?
- What is the expected default when deep scan warnings occur but no blocking findings exist?
- What acceptance rule should define "safe to merge" across mixed fast/deep/verification evidence?

### Data Model

- How long should local artifacts be retained?
- Should artifact schemas be versioned independently of package versions?
- Which artifacts are public API versus internal implementation detail?

### Security/Privacy

- Should QA-Z redact secret-like content from stdout/stderr tails?
- What data can safely appear in GitHub summaries and SARIF?
- What permission model is required if future remote integrations are added?

### Integrations

- Which CI providers are production targets beyond GitHub Actions?
- Which deep engines should follow Semgrep?
- Should GitHub annotations or bot comments be added, and under what permissions?

### UX Expectations

- Should QA-Z optimize for terse operator output, rich Markdown reports, machine JSON, or all three equally?
- Should missing tools be hard failures by default for every profile?
- How much explanation should repair prompts include for humans versus agent executors?

### Success Metrics

- What benchmark pass rate is required for release?
- What time budget is acceptable for default fast/deep runs?
- What user adoption or retention metric matters?

### Operations/Deployment

- What is the official release cadence?
- Should package registry publishing be part of production readiness?
- What remote repository and CI evidence is required before future releases?

## Evidence Sources

- `AGENTS.md`: human-confirmed mission, core command names, safety rails, documentation rules.
- `docs/superpowers/specs/2026-04-11-qa-z-bootstrap-design.md`: product definition brief and bootstrap scope.
- `README.md`: public product narrative, command workflow, current status, non-goals, docs index.
- `docs/architecture.md`: current architecture layers and model-agnostic boundary.
- `docs/mvp-issues.md`: historical MVP and alpha milestone scopes.
- `docs/releases/v0.9.8-alpha.md`: current alpha capabilities, validation evidence, and known non-goals.
- `docs/releases/v0.9.8-alpha-publish-handoff.md`: release gate, validation, generated-artifact, and publish safety evidence.
- `docs/artifact-schema-v1.md`: artifact schema and repair/verification contracts.
- `docs/repair-sessions.md`: repair session, executor bridge, executor-result, and autonomy boundaries.
- `docs/benchmarking.md`: benchmark corpus purpose, fixture contracts, and generated result policy.
- `docs/generated-vs-frozen-evidence-policy.md`: generated artifact policy.
- `qa-z.yaml` and `qa-z.yaml.example`: current config surface.
- `src/qa_z/cli.py` and `src/qa_z/commands/command_registry.py`: public command surface.
- `.github/workflows/ci.yml` and `.github/pull_request_template.md`: validation gates and contribution boundaries.
- `tests/`: current breadth of tests for CLI, runners, reporters, repair, verification, executor, benchmark, self-improvement, and release surfaces.
