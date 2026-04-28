QA-Z
> A deterministic QA control plane for coding agents.
![Status](https://img.shields.io/badge/status-alpha-orange)
![Release](https://img.shields.io/badge/release-v0.9.8--alpha-blue)
![Model agnostic](https://img.shields.io/badge/model--agnostic-yes-brightgreen)
QA-Z helps teams answer the question every coding-agent workflow eventually reaches:
Should this change be merged, and if not, what exactly should the agent fix next?
It turns issue/spec/diff context into QA contracts, runs deterministic fast and deep checks, and emits review, repair, verification, GitHub summary, and SARIF artifacts that humans or external agents can act on.
---
Why QA-Z?
Coding agents are good at changing code. Production teams still need traceable evidence.
QA-Z is designed to be:
QA-first: focused on merge readiness, not code generation.
Contract-first: every run can be tied back to explicit QA intent.
Deterministic-gated: pass/fail comes from executable checks, not LLM judgment.
Repair-oriented: failures become actionable repair packets.
Model-agnostic: works with Codex, Claude, human operators, or any external executor.
QA-Z is not another coding agent. It does not edit code, call live model APIs, create branches, push commits, or post GitHub comments by itself.
---
What it does
QA-Z can:
initialize a repository QA scaffold;
generate QA contracts from issue, spec, and diff inputs;
run deterministic Python and TypeScript fast checks;
run Semgrep-backed deep checks with SARIF output;
produce review packets and repair prompts from run artifacts;
package local repair sessions and executor handoffs;
ingest external executor results and verify candidate runs against baselines;
render compact GitHub Actions summaries;
run a seeded benchmark corpus for release confidence;
inspect QA-Z artifacts and select evidence-backed improvement tasks.
---
Quickstart
Install from source:
```bash
python -m pip install -e .[dev]
```
Inspect the CLI:
```bash
python -m qa_z --help
```
Initialize a repository:
```bash
python -m qa_z init --profile python --with-agent-templates
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
Run QA gates:
```bash
python -m qa_z fast --selection smart --diff changes.diff
python -m qa_z deep --selection smart --diff changes.diff
```
Generate review and repair artifacts:
```bash
python -m qa_z review --from-run latest
python -m qa_z repair-prompt --from-run latest --adapter codex
```
Verify a candidate repair:
```bash
python -m qa_z verify \
  --baseline-run .qa-z/runs/baseline \
  --candidate-run .qa-z/runs/candidate
```
If the `qa-z` console script is on your PATH, you can use `qa-z ...` instead of `python -m qa_z ...`.
---
Core workflow
```text
init
  -> plan
  -> fast
  -> deep
  -> review
  -> repair-prompt
  -> repair-session start
  -> external repair
  -> executor-result ingest
  -> verify
  -> github-summary
```
QA-Z keeps each step local and artifact-driven. The external repair step can be performed by a human, Codex, Claude, or another executor.
---
Command overview
Goal	Command
Bootstrap a repo	`qa-z init`
Validate config	`qa-z doctor`
Create QA contracts	`qa-z plan`
Run fast deterministic checks	`qa-z fast`
Run Semgrep-backed deep checks	`qa-z deep`
Render review packets	`qa-z review`
Generate repair prompts	`qa-z repair-prompt`
Create local repair sessions	`qa-z repair-session`
Compare baseline and candidate runs	`qa-z verify`
Render GitHub Actions summaries	`qa-z github-summary`
Run benchmark fixtures	`qa-z benchmark`
Inspect QA-Z evidence	`qa-z self-inspect`
Maintain/select backlog work	`qa-z backlog`, `qa-z select-next`
Prepare autonomy planning loops	`qa-z autonomy`
Package external executor handoffs	`qa-z executor-bridge`
Ingest external executor results	`qa-z executor-result`
---
Artifacts
QA-Z writes local artifacts under `.qa-z/` so later commands can reason from evidence instead of re-parsing terminal output.
Common outputs include:
```text
.qa-z/runs/<run-id>/summary.json
.qa-z/runs/<run-id>/summary.md
.qa-z/runs/<run-id>/deep/results.sarif
.qa-z/runs/<run-id>/review/packet.json
.qa-z/runs/<run-id>/repair/handoff.json
.qa-z/sessions/<session-id>/manifest.json
.qa-z/sessions/<session-id>/verify/compare.json
.qa-z/executor/<bridge-id>/bridge.json
.qa-z/executor-results/<result-id>/ingest.json
```
Root `.qa-z/**`, build outputs, caches, and benchmark result work directories are local by default and should not be committed unless intentionally frozen as evidence.
---
Deep checks and SARIF
`qa-z deep` runs configured `sg_scan` Semgrep checks when Semgrep is available on `PATH`.
It supports:
full or smart selection;
severity thresholds;
suppression policy;
grouped findings;
normalized JSON summaries;
SARIF 2.1.0 output for GitHub code scanning.
Default SARIF path:
```text
.qa-z/runs/<run-id>/deep/results.sarif
```
You can also write a stable SARIF path:
```bash
python -m qa_z deep --sarif-output qa-z.sarif
```
---
CI usage
QA-Z includes workflow templates for deterministic CI gates.
A typical CI flow runs:
```bash
python -m qa_z fast --selection smart --json
python -m qa_z deep --selection smart --json
python -m qa_z review --from-run latest
python -m qa_z repair-prompt --from-run latest
python -m qa_z github-summary --from-run latest
```
Deep findings can be uploaded as SARIF when the repository grants GitHub code-scanning permissions.
---
Alpha release gate
For QA-Z's own release checks:
```bash
python -m pytest
python scripts/alpha_release_gate.py --json
python scripts/alpha_release_artifact_smoke.py --with-deps --json
```
Current alpha validation baseline:
`pytest`: `1212 passed`
`ruff check`: passed
`ruff format --check`: passed
`mypy`: passed across `507` source files
alpha release gate: `29/29` passed
wheel/sdist install smoke: passed
artifact forbidden-file scan: `0` forbidden files
---
Status
QA-Z is currently in public alpha.
Implemented alpha scope:
local deterministic QA gates;
contract generation;
fast/deep run artifacts;
review and repair packets;
local repair sessions;
executor bridge packaging;
executor-result ingest;
post-repair verification;
GitHub summary and SARIF output;
benchmark and self-inspection workflows.
Not included in this alpha:
autonomous code editing;
live Codex or Claude execution;
remote queues, schedulers, or daemons;
automatic commits, pushes, or GitHub bot comments;
package-registry publishing.
---
Roadmap
Near-term priorities:
keep release evidence and docs synchronized;
expand deterministic benchmark coverage only where it adds unique evidence;
improve GitHub annotation surfaces beyond SARIF;
add more deep-check engines beyond Semgrep;
continue hardening executor-result safety and verification workflows.
Longer-term ideas:
property, mutation, and smoke-test deep checks;
richer PR annotations;
multi-engine security automation;
optional live executor integrations with strict safety boundaries.
---
Repository map
```text
docs/                 design notes, schemas, release notes, and workflow docs
qa/contracts/         QA contract workspace
src/qa_z/             Python package and CLI implementation
templates/            Codex, Claude, and workflow templates
.github/workflows/    repository CI workflows
examples/             Python and TypeScript demos
benchmarks/           seeded benchmark fixtures and support helpers
scripts/              release, smoke, and repository hygiene helpers
```
---
Learn more
Start with:
`qa-z.yaml.example` for the full public config shape;
`docs/artifact-schema-v1.md` for artifact fields;
`docs/repair-sessions.md` for local repair-session behavior;
`docs/pre-live-executor-safety.md` for executor safety boundaries;
`docs/releases/v0.9.8-alpha.md` for release notes.
---
Positioning
QA-Z is the QA layer for coding-agent workflows.
It helps agents, reviewers, and CI systems move from “the code changed” to “the change is tested, reviewed, repairable, and ready to evaluate.”
