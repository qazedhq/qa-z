# GitHub Repository Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this release plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish QA-Z as a public GitHub repository release candidate for `v0.9.8-alpha` without overstating current automation or committing generated local evidence.

**Architecture:** Treat GitHub launch as a deterministic release workflow around the existing local alpha baseline. The core work is repository remote setup, full evidence refresh, pull request validation, tag creation after merge, and post-release hygiene; no new product feature should be started during this sequence.

**Tech Stack:** Python 3.10+, setuptools build backend, pytest, ruff, mypy, Semgrep-backed QA-Z deep gate, GitHub Actions, SARIF upload, Git.

---

## Current Progress Snapshot

Audit date: 2026-04-20 KST.

Current branch:

```powershell
git status --short --branch
```

Observed:

```text
## codex/qa-z-bootstrap
```

Current release target:

- GitHub owner/repo: `qazedhq/qa-z`
- GitHub display name: `QA-Z`
- GitHub release: `v0.9.8-alpha`
- Python package version: `0.9.8a0`
- GitHub release title: `QA-Z v0.9.8-alpha`
- Prepared PR title: `Release QA-Z v0.9.8-alpha`
- Prepared PR body: `docs/releases/v0.9.8-alpha-pr.md`
- Prepared GitHub release body: `docs/releases/v0.9.8-alpha-github-release.md`
- Prepared release notes: `docs/releases/v0.9.8-alpha.md`
- Publish handoff: `docs/releases/v0.9.8-alpha-publish-handoff.md`

Direct validation performed in this audit:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest
python -m build --sdist --wheel
python scripts/alpha_release_artifact_smoke.py --json
python scripts/alpha_release_bundle_manifest.py --json
python scripts/alpha_release_gate.py --json
```

Observed results:

```text
ruff format: 134 files already formatted
ruff check: All checks passed!
mypy: Success: no issues found in 86 source files
pytest: 381 passed
build: qa_z-0.9.8a0.tar.gz and qa_z-0.9.8a0-py3-none-any.whl built
artifact smoke: wheel and sdist metadata install smoke passed
bundle manifest: bundle head and SHA256 artifact manifest generated
alpha release gate: one-shot local gate passed
```

Release blockers:

```powershell
git remote -v
```

Observed: no configured remote. A 2026-04-20 remote preflight reached GitHub for `https://github.com/qazedhq/qa-z.git` and returned `404 Not Found`, so the intended public repository still needs to be created or exposed before mutating local Git config. Do not create a tag until the intended GitHub repository exists, the branch or default branch is pushed, and remote CI passes.

## File Map

- `README.md`: Public product narrative, current command surface, alpha boundary, quickstart, and roadmap.
- `pyproject.toml`: Python package metadata; release version is `0.9.8a0`.
- `qa-z.yaml`: Repository-local Python-only release gate policy.
- `qa-z.yaml.example`: Public mixed Python/TypeScript config example.
- `.github/workflows/ci.yml`: Remote deterministic CI gate with test, package build, QA-Z fast/deep, SARIF upload, and artifact upload.
- `.github/workflows/codex-review.yml`: Review preparation workflow; does not perform live executor work.
- `docs/releases/v0.9.8-alpha-publish-handoff.md`: Source of truth for publish sequence and safety boundaries.
- `docs/releases/v0.9.8-alpha-pr.md`: PR body to use for the release PR.
- `docs/releases/v0.9.8-alpha-github-release.md`: GitHub release body to use after tagging.
- `docs/generated-vs-frozen-evidence-policy.md`: Artifact tracking policy for root `.qa-z/**` and benchmark results.
- `scripts/alpha_release_preflight.py`: Non-mutating local, public GitHub metadata, and empty-remote preflight before adding `origin`.
- `scripts/alpha_release_gate.py`: One-shot local alpha release gate that runs preflight, static checks, tests, CLI help smoke, QA-Z gates, build, artifact smoke, and bundle manifest evidence.
- `docs/reports/current-state-analysis.md`: Current capability and gap baseline.
- `docs/reports/next-improvement-roadmap.md`: Post-alpha improvement roadmap.
- `src/qa_z/**`: Product implementation.
- `tests/**`: Release regression suite.
- `benchmarks/fixtures/**`: Committed deterministic benchmark corpus.
- `templates/**` and `examples/**`: Public downstream templates and runnable/placeholder examples.

## Phase 0: Name And Version Contract

- [ ] **Step 1: Freeze the public naming contract**

Use this launch contract unless the repository owner namespace is unavailable at final GitHub creation time:

- Owner slug: `qazedhq`
- Repository slug: `qa-z`
- Public brand: `QA-Z`
- Python package name: `qa-z`
- Python import name: `qa_z`

Expected:

```text
Public docs, GitHub repository settings, and release copy all use QA-Z / qa-z / qa_z consistently.
```

- [ ] **Step 2: Freeze the release version contract**

Use:

- Git tag: `v0.9.8-alpha`
- GitHub release title: `QA-Z v0.9.8-alpha`
- Python package version: `0.9.8a0`

Expected:

```text
Release notes and the GitHub release body explicitly say "Python package version is 0.9.8a0" so the human-friendly alpha tag and PEP 440 package version cannot be confused.
```

## Phase 1: Repository Target And Remote Preflight

- [ ] **Step 1: Create or choose the intended GitHub repository**

Use `qazedhq/qa-z` if GitHub's account or organization creation screen still accepts the owner slug. If unavailable, stop and choose a replacement before publishing because owner/repo slugs should be treated as near-permanent public API.

Required repository settings:

- Visibility selected intentionally: public for launch, private only for a pre-launch rehearsal.
- GitHub Actions enabled.
- Code scanning enabled or allowed to accept SARIF upload once permissions are available.
- Private vulnerability reporting enabled if the repository settings support it.
- Default branch policy decided before merge, usually `main`.
- Branch protection can be added after first remote CI pass if the initial push needs bootstrapping.

- [ ] **Step 2: Verify the target repository URL before mutating local Git config**

Run:

```powershell
python scripts/alpha_release_preflight.py --repository-url <repository-url>
git ls-remote --refs <repository-url>
```

Expected for an empty but reachable repository:

```text
Preflight confirms public GitHub metadata for the intended owner/repo. No authentication or not-found error. `git ls-remote --refs` output is empty because no refs exist.
```

Expected for an existing repository:

```text
The command prints existing remote refs. Stop before adding origin; if this is the intended default-branch or bootstrap-commit repository, rerun `python scripts/alpha_release_preflight.py --repository-url <repository-url> --allow-existing-refs` and then use the release PR path.
```

- [ ] **Step 3: Add `origin` only after the URL is verified**

Run:

```powershell
git remote add origin <repository-url>
git remote -v
git status --short --branch
```

Expected:

```text
origin points at the intended GitHub repository.
Working tree remains clean except ignored local build or runtime artifacts.
```

## Phase 2: Final Local Release Evidence Refresh

- [ ] **Step 0: Run the one-shot local alpha release gate**

Run:

```powershell
python scripts/alpha_release_gate.py --json
```

Expected:

```text
The local preflight, static checks, tests, CLI help smoke, QA-Z
fast/deep/benchmark, package build, artifact smoke, and bundle manifest phases
all pass with one JSON result and one exit code.
```

- [ ] **Step 1: Confirm generated artifacts are still ignored**

Run:

```powershell
python scripts/alpha_release_preflight.py --skip-remote
git status --short --ignored
git ls-files | Where-Object { $_ -like '.qa-z/*' -or $_ -like 'benchmarks/results/*' -or $_ -like '*.pyc' -or $_ -like '.pytest_cache/*' -or $_ -like '.mypy_cache/*' -or $_ -like '.ruff_cache/*' -or $_ -like 'src/qa_z.egg-info/*' }
```

Expected:

```text
No tracked root .qa-z artifacts, benchmark result snapshots, caches, pyc files, or egg-info files.
Preflight confirms the release branch, missing origin, absent release tag, clean worktree, and generated artifact hygiene before remote mutation.
```

- [ ] **Step 2: Run the static and unit-test baseline**

Run:

```powershell
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
python -m pytest
```

Expected:

```text
All commands pass. The expected current pytest count is 381 passed.
```

- [ ] **Step 3: Run the QA-Z local release gate**

Run:

```powershell
python -m qa_z fast --selection smart --json
python -m qa_z deep --selection smart --json
python -m qa_z benchmark --json
```

Expected:

```text
fast passes with Python checks.
deep passes with Semgrep results normalized and no blocking findings for the release baseline.
benchmark passes all committed fixtures; the latest recorded release handoff expects 50/50 fixtures and overall_rate 1.0.
```

- [ ] **Step 4: Rebuild package artifacts**

Run:

```powershell
python -m build --sdist --wheel
python scripts/alpha_release_artifact_smoke.py --json
```

Expected:

```text
dist/qa_z-0.9.8a0.tar.gz
dist/qa_z-0.9.8a0-py3-none-any.whl
artifact smoke passes for wheel and sdist metadata install checks
```

- [ ] **Step 5: Regenerate and verify a local Git bundle for handoff**

Run:

```powershell
git bundle create dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle codex/qa-z-bootstrap
git bundle verify dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle
git bundle list-heads dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle
git rev-parse HEAD
Get-FileHash -Algorithm SHA256 dist\qa_z-0.9.8a0.tar.gz,dist\qa_z-0.9.8a0-py3-none-any.whl,dist\qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle
python scripts/alpha_release_bundle_manifest.py --json
```

Expected:

```text
Bundle verifies successfully.
Bundle head points at codex/qa-z-bootstrap.
Hashes are recorded in the release operator notes if artifacts will be attached.
The bundle manifest command emits the same head and SHA256 evidence as JSON.
```

## Phase 3: Push Default Branch Or Open Release PR

- [ ] **Step 1: Choose the first remote validation path**

If `qazedhq/qa-z` is a brand-new empty repository, a release PR is optional for the first public baseline. Prefer pushing the current release baseline to the default branch first so GitHub Actions, code scanning, artifacts, README rendering, and repository health checks can run against the branch GitHub treats as canonical.

If the repository already has a default branch or a pre-launch bootstrap commit, use the PR path instead.
Confirm that this path was selected intentionally by rerunning the remote
preflight with `--allow-existing-refs` before adding `origin`.

Expected:

```text
The first remote validation path is explicit before any push.
```

- [ ] **Step 2A: Empty-repository path, push the default branch first**

Run:

```powershell
git push -u origin HEAD:main
```

Expected:

```text
The repository default branch has the release baseline and remote CI starts from the canonical branch.
```

- [ ] **Step 2B: Existing-default-branch path, push the release branch**

Run:

```powershell
git push -u origin codex/qa-z-bootstrap
```

Expected:

```text
The branch appears on GitHub and tracks origin/codex/qa-z-bootstrap.
```

- [ ] **Step 3: Open the release PR if using the PR path**

Use:

- Base branch: `main`
- Head branch: `codex/qa-z-bootstrap`
- Title: `Release QA-Z v0.9.8-alpha`
- Body source: `docs/releases/v0.9.8-alpha-pr.md`

Expected:

```text
The PR clearly states alpha scope, validation evidence, generated artifact policy, and known non-goals.
```

- [ ] **Step 4: Confirm remote CI starts**

Inspect GitHub Actions for:

- `test` job
- `qa-z` job
- package build step inside `test`
- SARIF upload step inside `qa-z`
- QA-Z artifact upload step inside `qa-z`

Expected:

```text
Remote CI runs on the pushed release branch or release PR.
```

## Phase 4: Remote CI Triage

- [ ] **Step 1: Require the deterministic jobs to pass**

Required passing surfaces:

- `python -m pytest`
- `python -m build --sdist --wheel`
- `python scripts/alpha_release_artifact_smoke.py --json`
- `python -m qa_z fast --selection smart --json`
- `python -m qa_z deep --selection smart --json`
- final fast/deep verdict aggregation step

Expected:

```text
Both the test job and qa-z job pass, except SARIF upload may be continue-on-error if repository permissions are not ready.
```

- [ ] **Step 2: Treat SARIF permission failures as setup work, not product failure**

If `github/codeql-action/upload-sarif@v3` fails with a permission or code-scanning setup issue, confirm:

- The `deep/results.sarif` artifact exists in uploaded QA-Z run artifacts.
- The workflow step is marked `continue-on-error`.
- The final QA-Z fast/deep verdict step still reflects actual gate status.

Expected:

```text
The PR can proceed if deterministic gates pass and only code-scanning publication is blocked by repository settings.
```

- [ ] **Step 3: Fix any remote-only failure with normal TDD discipline**

If a CI failure appears that did not reproduce locally:

```powershell
git pull --ff-only
python -m pytest
python -m qa_z fast --selection smart --json
python -m qa_z deep --selection smart --json
python -m qa_z benchmark --json
```

Expected:

```text
The failure is reproduced or isolated. Any Python behavior change gets a failing test first, then implementation, then the full affected gate.
```

## Phase 5: Merge, Tag, And GitHub Release

- [ ] **Step 1: Merge the release PR only after remote CI is acceptable, if using the PR path**

Expected:

```text
The merged commit or first validated default-branch commit is the release baseline for tagging.
```

- [ ] **Step 2: Update local `main` and tag the merged release baseline**

Run:

```powershell
git checkout main
git pull --ff-only origin main
git tag -s v0.9.8-alpha -m "QA-Z v0.9.8-alpha"
git tag -v v0.9.8-alpha
git push origin v0.9.8-alpha
```

Expected:

```text
Signed tag v0.9.8-alpha exists on GitHub and points at the validated release baseline.
```

If tag signing is not configured for this alpha, use an annotated tag instead and record the reason in the operator notes:

```powershell
git tag -a v0.9.8-alpha -m "QA-Z v0.9.8-alpha"
```

- [ ] **Step 3: Create the GitHub release**

Use:

- Tag: `v0.9.8-alpha`
- Title: `QA-Z v0.9.8-alpha`
- Body source: `docs/releases/v0.9.8-alpha-github-release.md`
- Optional attachments: rebuilt `dist/qa_z-0.9.8a0.tar.gz`, `dist/qa_z-0.9.8a0-py3-none-any.whl`, and the verified bundle if desired.

Expected:

```text
The GitHub release clearly describes the alpha as local deterministic QA control-plane tooling, not live autonomous execution.
```

## Phase 6: Post-Launch Hygiene

- [ ] **Step 1: Confirm public landing surfaces**

Check these pages in GitHub after release:

- Repository README renders correctly.
- License is detected as Apache-2.0.
- Security policy is visible.
- Private vulnerability reporting is enabled or explicitly deferred.
- Community standards checklist has no unexpected gaps for the alpha baseline.
- Issue templates are visible.
- Pull request template is visible.
- Actions tab shows the latest passing or understood release workflow.
- Release page points at `v0.9.8-alpha`.

Expected:

```text
The repository can be understood by a new visitor without opening local-only artifacts.
```

- [ ] **Step 2: Keep generated output out of source history**

Run:

```powershell
git status --short
git ls-files | Where-Object { $_ -like '.qa-z/*' -or $_ -like 'benchmarks/results/*' -or $_ -like 'dist/*' -or $_ -like 'build/*' -or $_ -like '*.pyc' }
```

Expected:

```text
No local runtime artifacts are tracked unless a future release explicitly freezes evidence with surrounding context.
```

- [ ] **Step 3: Open post-alpha planning issues from existing roadmap**

Create GitHub issues from the already documented roadmap, not from vague future promises:

- Broaden mixed-surface benchmark breadth.
- Keep report, template, and example current-truth sync.
- Deepen executor operator diagnostics while staying live-free.
- Maintain generated versus frozen evidence policy as artifact surfaces evolve.
- Maintain loop-health summary clarity as autonomy surfaces grow.
- Consider standalone GitHub annotations only after SARIF/code-scanning release behavior is stable.

Expected:

```text
Issues are scoped to deterministic QA evidence and do not imply live Codex or Claude automation.
```

## Launch Readiness Assessment

Ready now:

- Core command surface exists and matches the README command list.
- Public README, CONTRIBUTING, SECURITY, PR template, issue templates, CI workflow, and release docs are present.
- Local static checks, type checks, tests, and package build pass in this audit.
- The generated artifact policy is explicit in `.gitignore`, docs, release handoff, and PR template.
- Release PR and GitHub release bodies are already prepared.

Not ready until resolved:

- `qazedhq/qa-z` has not been created or exposed as a reachable public GitHub repository; the 2026-04-20 remote preflight returned `404 Not Found`.
- No `origin` remote is configured.
- No `v0.9.8-alpha` tag exists.
- Remote GitHub Actions evidence does not exist yet for the target repository.
- Code scanning/SARIF publication needs repository-side confirmation.

Decision:

```text
QA-Z is locally release-ready for a public v0.9.8-alpha repository launch after the GitHub repository target is configured and remote CI passes.
```
