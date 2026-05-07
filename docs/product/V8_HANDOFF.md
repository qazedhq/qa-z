# V8 Handoff Context

## Product Identity

- Product name: QA-Z.
- Product category: local QA control plane for coding-agent workflows.
- One-sentence description: QA-Z helps developers decide whether agent-produced code is safe to merge by turning change context into QA contracts, deterministic gates, local artifacts, repair handoffs, and post-repair verification evidence.
- Current maturity: alpha, package metadata `0.9.8a0`, release docs for `v0.9.8-alpha`.

## Authoritative Product Goal

The production goal is to deliver a reliable local QA control plane for developers, code reviewers, and coding-agent operators that lets them decide whether agent-produced code is safe to merge through contract generation, deterministic fast/deep gates, artifact-backed review, repair handoff, post-repair verification, CI summaries, SARIF, benchmark coverage, and local self-improvement planning, with production-grade security, reliability, testing, deployment, observability through artifacts, data integrity, documentation, and maintainability appropriate for local repositories and CI pipelines.

## Human-Confirmed Direction

- QA-Z is Codex-first and model-agnostic.
- Preserve core command names: `init`, `plan`, `fast`, `deep`, `review`, `repair-prompt`.
- Prefer executable quality gates over vague advice.
- Prefer explicit contracts over implied requirements.
- Prefer deterministic evidence over stylistic guesswork.
- Prefer repairable feedback over raw failure dumps.
- Treat Codex and Claude integrations as adapters, not the core engine.
- Do not claim deep QA automation beyond what runners and tests prove.
- Do not replace deterministic pass/fail checks with LLM-only judgment.
- Do not add hidden network dependencies to local QA flows.

## Target Users

- Primary users: developers, maintainers, and code reviewers using AI coding agents.
- Secondary users: QA/security reviewers, CI maintainers, and release operators.
- Advanced users: external executor operators using repair-session, executor-bridge, executor-result, and verification artifacts.
- Unknown: buyer/customer profile and hosted/team product direction.

## Core Workflows V8 Must Protect

| Flow | Why it matters | Evidence | Existing tests/E2E |
| --- | --- | --- | --- |
| `init -> plan -> fast` | Activation and first deterministic gate | README quickstart, CLI help, bootstrap/fast source | CLI, bootstrap, config, fast selection tests |
| `deep -> SARIF` | Security/risk evidence and code scanning | README, artifact schema, CI SARIF upload | deep, Semgrep normalization, SARIF tests |
| `review -> repair-prompt` | Converts raw failures into human/agent repair guidance | README, artifact schema, repair docs | review, repair prompt, repair handoff tests |
| `verify` baseline/candidate | Prevents false repair completion claims | README, verification modules | verification comparison tests and benchmark fixtures |
| `repair-session -> executor-bridge -> executor-result` | Safe external executor boundary without live orchestration | repair sessions docs, pre-live safety docs | session, bridge, executor-result, dry-run tests |
| `benchmark` | Measures control-plane behavior across seeded fixtures | benchmarking docs, release evidence | benchmark tests and fixture contracts |
| `self-inspect -> select-next -> autonomy` | Evidence-backed self-improvement planning without source editing | README, autonomy docs/source | self-improvement and autonomy tests |
| release/readiness gates | Keeps public alpha evidence truthful | release handoff, CI, scripts | release gate/preflight/artifact smoke tests |

## Product Non-Goals

- Do not add live Codex, Claude, or other model API execution.
- Do not make QA-Z edit source code autonomously.
- Do not add queues, schedulers, remote workers, daemons, or hosted orchestration without human approval.
- Do not add automatic commits, pushes, branch creation, deployments, GitHub bot comments, or Checks API mutations.
- Do not move agent-specific logic into core planner/runners.
- Do not make LLM-only review a pass/fail authority.
- Do not weaken generated-artifact policy by committing root `.qa-z/**` or benchmark results unless intentionally frozen with context.
- Do not redesign the public command surface without explicit approval.
- Do not introduce billing, accounts, team administration, or UI/dashboard scope without confirmation.

## Production Readiness Gates For This Project

| Gate | Why it matters | How V8 should validate it | Known gaps |
| --- | --- | --- | --- |
| Build/runtime | Package must install and CLI must run | `python -m build --sdist --wheel`; artifact smoke scripts; CLI help smoke | Local build may depend on environment and generated artifacts |
| Tests | Python behavior is heavily test-backed | `python -m pytest`; focused tests for touched docs/source surfaces | Broad test suite can be expensive and current worktree is dirty |
| Fast/deep QA-Z gates | Product must dogfood deterministic gates | `python -m qa_z fast --selection smart --json`; `python -m qa_z deep --selection smart --json` | Semgrep/tool availability can block local deep runs |
| Benchmark | Measures product contract behavior | `python -m qa_z benchmark --json` | One results dir can be locked; generated results stay local |
| Security/privacy | Local flows must avoid hidden network and secret leaks | inspect workflow/config changes; run security/deep gates when behavior changes | Redaction policy for stdout/stderr tails needs product confirmation |
| Data integrity | Artifact schemas and generated policy are public product contracts | artifact schema tests; generated-artifact policy checks; release gate | Which artifacts are public API needs explicit versioning policy |
| API/CLI contract | Command names and artifact paths are product-critical | CLI help tests and public docs guard tests | New commands can dilute core workflow if not documented |
| UX/error states | Failures must be repairable, not raw dumps | tests for missing tools, invalid config, stale artifacts, executor-result mismatch | Need continued focus on concise operator guidance |
| Observability | Artifacts are the observability layer | inspect `.qa-z/**` summaries, gate JSON, SARIF, GitHub summary | No hosted telemetry by design |
| CI/CD | CI must preserve evidence and fail on recorded exits | inspect `.github/workflows/ci.yml`; run release preflight/gate when release scope changes | GitHub write integrations are intentionally limited |
| Documentation | README/config/docs must match implementation | docs current-truth tests, docs review, markdown sanity | Product direction docs are new and should remain linked from docs index |

## Recommended First V8 Improvement Loop

- Objective: protect and harden the primary merge-readiness loop: `plan -> fast -> deep -> review -> repair-prompt`.
- Why this loop is first: it is the product's core promise and the first place user trust is won or lost.
- Candidate files/areas: README command examples, `docs/artifact-schema-v1.md`, `src/qa_z/commands/execution_runs.py`, `src/qa_z/runners/fast.py`, `src/qa_z/runners/deep.py`, `src/qa_z/reporters/review_packet*.py`, `src/qa_z/reporters/repair_prompt*.py`, fast/deep/review/repair tests.
- Suggested validation: focused tests for touched modules, then `python -m qa_z fast --selection smart --json`, `python -m qa_z deep --selection smart --json` when Semgrep is available, and relevant benchmark fixtures.
- Risk notes: do not change public artifact shape casually; do not weaken deterministic failure status to make examples green.

## Recommended Second V8 Improvement Loop

- Objective: harden post-repair truth: repair-session, executor-bridge, executor-result ingest, and `verify`.
- Why this loop is second: QA-Z must be able to reject stale, partial, or regressed repair claims before external executor workflows expand.
- Candidate files/areas: `docs/repair-sessions.md`, `docs/pre-live-executor-safety.md`, `src/qa_z/repair_session*.py`, `src/qa_z/executor_bridge*.py`, `src/qa_z/executor_result*.py`, `src/qa_z/verification*.py`, executor and verification tests.
- Suggested validation: targeted executor/verification tests, dry-run fixture tests, and `qa-z verify`/repair-session CLI smoke flows using disposable fixture runs.
- Risk notes: keep bridge/result ingest live-free; returned executor data is evidence, not trust.

## Recommended Third V8 Improvement Loop

- Objective: keep release/current-truth and benchmark evidence aligned with the actual product surface.
- Why this loop is third: production readiness depends on avoiding stale docs, stale examples, and benchmark gaps.
- Candidate files/areas: `docs/current-truth-maintenance-anchors.md`, release docs, `docs/generated-vs-frozen-evidence-policy.md`, `docs/benchmarking.md`, `benchmarks/fixtures/**/expected.json`, `scripts/alpha_release_gate.py`, public docs tests.
- Suggested validation: docs/current-truth tests, `python -m qa_z benchmark --json`, release gate scripts when release behavior changes.
- Risk notes: generated benchmark results are local by default; do not stage runtime artifacts as proof.

## Validation Commands

Validation safety classes:

- Read-only/lightweight probes: CLI help, `doctor --json`, and focused static inspections.
- Local artifact-writing gates: `fast`, `deep`, `benchmark`, release gate scripts, and repair/session smoke flows; use isolated output directories when running them in parallel or from automation.
- Tool/network-dependent gates: Semgrep-backed `deep` requires Semgrep to be installed and may depend on the configured Semgrep rule source; do not hide install or rule-resolution requirements inside local QA flows.
- Release/package gates: build, artifact smoke, and release preflight are appropriate for release-readiness loops, but publishing, tagging, deployment, or remote mutation still requires separate human action.

| Command | Purpose | Working directory | Confidence | Notes |
| --- | --- | --- | --- | --- |
| `python -m pip install -e .[dev]` | install local development package | repo root | high | documented in README/AGENTS/CONTRIBUTING |
| `python -m qa_z --help` | smoke public CLI command surface | repo root | high | verified during this documentation pass |
| `python -m qa_z doctor --json` | validate config/onboarding state | repo root | medium | safe read-style validation; strict mode can fail on warnings |
| `python -m pytest` | full Python behavior gate | repo root | high | required after Python source/test edits and useful after workflow/test-contract changes |
| `python -m ruff format --check src tests scripts` | formatting gate | repo root | high | CI/release docs use `src tests scripts` |
| `python -m ruff check src tests scripts` | lint gate | repo root | high | CI/release docs use `src tests scripts` |
| `python -m mypy src tests` | type gate | repo root | high | CI/release docs use this |
| `python -m qa_z fast --selection smart --json` | product fast gate | repo root | high | writes `.qa-z/**` runtime artifacts |
| `python -m qa_z deep --selection smart --json` | product deep gate | repo root | medium-high | requires Semgrep for configured deep checks |
| `python -m qa_z benchmark --json` | seeded product contract benchmark | repo root | high | writes local benchmark results; one results dir lock at a time |
| `python scripts/alpha_release_gate.py --json` | one-shot alpha release gate | repo root | high | broad release validation; use for release-readiness loops |
| `python scripts/alpha_release_artifact_smoke.py --json` | package artifact smoke | repo root | high | follows package build |
| `python scripts/alpha_release_preflight.py --skip-remote --json` | local release preflight | repo root | high | remote checks are separate and may require access |

## Suggested E2E / Browser Flows

QA-Z is CLI/artifact-first and has no browser UI in this repository. V8 should prioritize safe CLI E2E flows:

| Flow | Preconditions | Safety constraints | Expected result | Current evidence |
| --- | --- | --- | --- | --- |
| Python demo passing flow | editable install, example dependencies as documented | run inside `examples/fastapi-demo`; keep generated `.qa-z/**` local | `plan`, `fast`, `review`, `repair-prompt` complete with local artifacts | examples README and README preview |
| Python demo failing repair packet | `examples/fastapi-demo/qa-z.failing.yaml` | expected failure, do not call it a broken demo | failed fast run produces repairable packet | examples README |
| TypeScript fast demo | Node dependencies installed in `examples/typescript-demo` | do not change package manager behavior without approval | ESLint, `tsc`, and Vitest checks flow through QA-Z | examples README and config |
| Deep/SARIF run | Semgrep installed | no hidden install; preserve non-blocking scan warnings | deep summary and `results.sarif` generated | artifact schema and CI workflow |
| Repair-session verification | baseline/candidate run artifacts available | QA-Z does not edit candidate source | session outcome records deterministic verify verdict | repair sessions docs |
| Benchmark selected fixture | no active benchmark lock in results dir | use isolated results dir when parallel work is possible | selected fixture passes expected contract | benchmark docs |
| Release gate rehearsal | release scope change or readiness loop | do not publish/push/tag from QA-Z | JSON gate records pass/fail and next actions | release handoff |

## Known Risks And Unknowns

- The working tree may be intentionally dirty; V8 must preserve unrelated changes.
- `rg.exe` may fail with access denied on this Windows workstation; use PowerShell or `git grep` fallback.
- Generated artifacts under `.qa-z/**`, `benchmarks/results/**`, `build/**`, `dist/**`, and caches can appear during validation and should stay unstaged unless explicitly frozen.
- Semgrep availability can make deep validation environment-dependent.
- Public product direction beyond local CLI and CI is not fully confirmed.
- Hosted service, UI, billing, team administration, and write-enabled GitHub automation are not approved.
- Some release evidence in docs is historical and must be refreshed before making current readiness claims.

## Human Decisions Required Before Aggressive Remediation

- Confirm whether QA-Z should remain CLI/local-first or add hosted/team workflows.
- Confirm whether GitHub bot comments, Checks API publishing, or write permissions are ever in scope.
- Confirm production language support requirements beyond Python and TypeScript.
- Confirm which deep engines should follow Semgrep.
- Confirm artifact retention, redaction, and privacy policy for stdout/stderr tails.
- Confirm package registry publishing and release cadence.
- Confirm whether repair-session/executor-bridge is core product scope or advanced/operator scope.

## Pasteable V8 Context Block

```text
Product: QA-Z, a Codex-first, model-agnostic local QA control plane for coding-agent workflows.
Goal: help developers and reviewers decide whether agent-produced code is safe to merge through QA contracts, deterministic fast/deep gates, local artifacts, review packets, repair handoffs, post-repair verification, CI summaries, SARIF, benchmarks, and local self-improvement planning.
Target users: developers, maintainers, code reviewers, QA/security reviewers, CI maintainers, and release operators using coding agents.
Core workflows to protect: init -> plan -> fast -> deep -> review -> repair-prompt; verify baseline/candidate; repair-session -> executor-bridge -> executor-result; benchmark; self-inspect/select-next/autonomy; release/readiness gates.
Non-goals: no live model execution, no autonomous code editing, no remote orchestration, no automatic commits/pushes/branches/deployments/GitHub bot comments, no LLM-only pass/fail authority, no hidden network dependencies.
Highest-priority gates: pytest and focused tests for touched Python, QA-Z fast/deep gates, benchmark fixtures, artifact schema/current-truth checks, release gate for release-scope changes, generated-artifact policy.
First improvement loop: harden the primary merge-readiness loop (`plan -> fast -> deep -> review -> repair-prompt`) with artifact-preserving tests and docs alignment.
Human decisions still needed: hosted/team scope, write-enabled GitHub integrations, deep-engine roadmap, artifact redaction/retention policy, package publishing cadence, and whether executor bridge is core or advanced product scope.
```
