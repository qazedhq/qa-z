QA-Z ⚡
Codex-first QA control plane for coding-agent workflows.
QA-Z turns code changes into QA contracts, runs deterministic checks, and produces review / repair / verification artifacts that humans and coding agents can act on.
![CI](https://github.com/qazedhq/qa-z/actions/workflows/ci.yml/badge.svg)
![Status](https://img.shields.io/badge/status-alpha-orange)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![QA](https://img.shields.io/badge/QA-contract--first-purple)
![Release](https://img.shields.io/badge/release-v0.9.8--alpha-brightgreen)
---
✨ What is QA-Z?
Most coding agents are built to write code.
QA-Z is built to answer the next question:
> **Should this change be merged — and if not, what should the agent fix next?**
QA-Z gives your repo a local, deterministic QA layer that can:
🧾 generate QA contracts from issues, specs, and diffs
⚡ run fast checks for Python and TypeScript projects
🔎 run Semgrep-backed deep checks
🧠 produce review packets and repair prompts
🛠️ package repair sessions for Codex, Claude, or human operators
✅ verify whether a repair actually improved the result
📦 emit GitHub summaries, SARIF, benchmark reports, and local artifacts
---
🚀 Quickstart
Install QA-Z locally:
```bash
python -m pip install -e .[dev]
```
Check the CLI:
```bash
python -m qa_z --help
```
Initialize a repo:
```bash
python -m qa_z init --profile python --with-agent-templates --with-github-workflow
```
Validate the config:
```bash
python -m qa_z doctor
```
Create a QA contract:
```bash
python -m qa_z plan \
  --title "Protect billing auth guard" \
  --issue issue.md \
  --spec spec.md \
  --diff changes.diff
```
Run the fast gate:
```bash
python -m qa_z fast --selection smart --diff changes.diff
```
Run the deep gate:
```bash
python -m qa_z deep --selection smart --diff changes.diff
```
Generate a review packet:
```bash
python -m qa_z review --from-run latest
```
Generate an agent-ready repair prompt:
```bash
python -m qa_z repair-prompt --from-run latest --adapter codex
```
---
🧭 Core workflow
```text
init
  ↓
plan
  ↓
fast
  ↓
deep
  ↓
review
  ↓
repair-prompt
  ↓
external repair
  ↓
verify
  ↓
github-summary
```
QA-Z does not edit your code by itself.
It creates the contracts, evidence, prompts, and verification artifacts that make external repair work safer and easier to review.
---
🧩 Command surface
Command	What it does
`qa-z init`	Create starter QA-Z config and optional templates
`qa-z doctor`	Validate config shape and launch readiness
`qa-z plan`	Generate a QA contract from issue/spec/diff input
`qa-z fast`	Run deterministic fast checks
`qa-z deep`	Run configured Semgrep deep checks
`qa-z review`	Render a review packet from run artifacts
`qa-z repair-prompt`	Generate Codex / Claude / handoff repair prompts
`qa-z repair-session`	Package a local repair workflow
`qa-z verify`	Compare baseline and candidate run artifacts
`qa-z github-summary`	Render GitHub Actions summary Markdown
`qa-z benchmark`	Run seeded QA-Z benchmark fixtures
`qa-z self-inspect`	Inspect QA-Z artifacts and surface improvement tasks
`qa-z select-next`	Select the next evidence-backed improvement task
`qa-z backlog`	Refresh or inspect the improvement backlog
`qa-z autonomy`	Run deterministic local planning loops
`qa-z executor-bridge`	Package a loop/session for an external executor
`qa-z executor-result`	Ingest and audit external executor results
---
⚡ Fast checks
QA-Z can run configured fast checks and store the results under `.qa-z/runs/`.
Typical checks include:
Python lint, format, typecheck, and tests
TypeScript lint, typecheck, and tests
full or smart diff-aware selection
strict no-tests policy support
JSON and Markdown artifacts
Example:
```bash
python -m qa_z fast --json
python -m qa_z fast --selection smart --diff changes.diff
```
---
🔎 Deep checks
QA-Z deep checks currently focus on Semgrep-backed static analysis.
Deep runs can:
attach to the latest fast run
run standalone into a chosen output directory
target changed source/test files in smart mode
escalate risky or ambiguous changes to a full scan
emit normalized findings and SARIF
Example:
```bash
python -m qa_z deep --from-run latest
python -m qa_z deep --sarif-output qa-z.sarif
```
Default SARIF output:
```text
.qa-z/runs/<run-id>/deep/results.sarif
```
---
🛠️ Repair workflow
QA-Z turns failed checks and blocking deep findings into repair-ready artifacts.
```bash
python -m qa_z repair-prompt --from-run latest --adapter codex
```
Generated artifacts include:
```text
.qa-z/runs/<run-id>/repair/handoff.json
.qa-z/runs/<run-id>/repair/codex.md
.qa-z/runs/<run-id>/repair/claude.md
```
These files are designed for:
Codex
Claude
a human reviewer
another external coding executor
QA-Z itself does not call live model APIs.
---
✅ Verification
After a repair, QA-Z can compare a baseline run with a candidate run.
```bash
python -m qa_z verify \
  --baseline-run .qa-z/runs/baseline \
  --candidate-run .qa-z/runs/candidate
```
Possible verdicts:
`improved`
`unchanged`
`mixed`
`regressed`
`verification_failed`
---
📦 Artifacts
QA-Z is artifact-first.
Most outputs are written under:
```text
.qa-z/
```
Common artifact surfaces:
Path	Purpose
`.qa-z/runs/`	Fast/deep run evidence
`.qa-z/sessions/`	Local repair sessions
`.qa-z/executor/`	External executor bridge packages
`.qa-z/executor-results/`	Returned executor result ingest artifacts
`.qa-z/improvement/`	Self-inspection and backlog artifacts
`.qa-z/loops/`	Autonomy planning loop artifacts
Root `.qa-z/**` is local by default and should normally stay out of release commits.
---
🧪 Validation status
Current alpha validation evidence:
```text
ruff check src tests scripts: passed
ruff format --check src tests scripts: 519 files already formatted
mypy src tests: passed across 507 source files
pytest: 1212 passed
alpha release gate: 29/29 passed
artifact smoke: wheel and sdist passed
artifact forbidden scan: 0 forbidden files
GitHub Actions: test success, qa-z success
```
Release tag:
```text
v0.9.8-alpha
```
---
🧱 What QA-Z is not
QA-Z is intentionally not:
❌ a coding agent
❌ an autonomous code editor
❌ a live Codex or Claude runtime
❌ a queue, scheduler, or remote orchestrator
❌ an LLM-only judge replacing deterministic checks
❌ a tool that commits, pushes, or posts GitHub comments by itself
QA-Z is the QA layer around those workflows.
---
🗺️ Roadmap
Near-term roadmap:
🧪 broader TypeScript deep QA automation
🔐 multi-engine security checks
🧬 property, mutation, smoke, and e2e test integrations
🧾 richer GitHub Checks / annotation support
📊 stronger benchmark realism for mixed Python + TypeScript repos
🛡️ tighter release evidence and artifact hygiene flows
---
📚 Docs
Useful starting points:
```text
docs/artifact-schema-v1.md
docs/repair-sessions.md
docs/pre-live-executor-safety.md
docs/generated-vs-frozen-evidence-policy.md
qa-z.yaml.example
examples/typescript-demo/
```
---
💡 Positioning
QA-Z is not another coding agent.
It is the QA control plane that helps coding agents reach production quality with:
traceable contracts
executable checks
reviewable evidence
actionable repair feedback
deterministic verification
