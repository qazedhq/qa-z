# Package Publish Plan

The user-facing install path should move from source checkout to one-line install without overclaiming a package that is not published yet.

## v0.9.8-alpha

- GitHub prerelease.
- Source install.
- Git tag install:

```bash
pipx install "git+https://github.com/qazedhq/qa-z.git@v0.9.8-alpha"
uv tool install "git+https://github.com/qazedhq/qa-z.git@v0.9.8-alpha"
```

## v0.9.9-alpha

- GitHub prerelease.
- No PyPI, TestPyPI, npm, GitHub Packages, or other package registry publish.
- Git tag install:

```bash
pipx install "git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha"
uv tool install "git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha"
```

- Release artifact smoke used `python scripts/alpha_release_artifact_smoke.py --with-deps --json`.

## Alpha RC package dry-run packet - 2026-05-12

Package metadata version: `0.9.8a0`.
Current release proof HEAD: `1ede65172f770c66159b2cc5e9e7d4f2063bf634`.

No PyPI, TestPyPI, npm, GitHub Packages, or other package registry publish is approved.
`RELEASE_EXECUTION_APPROVED` and `PACKAGE_PUBLISH_ALLOWED` must both be set to
`true` by a human release owner before any upload command is run.
The proof HEAD must have proof-branch remote CI and public raw evidence before
any package upload command becomes eligible for release-owner approval.

Safe local-only dry-run packet:

```bash
git status --short -uall
python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting
python scripts\alpha_release_gate.py --quick --allow-dirty --json
python -m build --sdist --wheel
python scripts\alpha_release_artifact_smoke.py --with-deps --json
python scripts\package_smoke_rehearsal.py --json --allow-missing-tools
```

The dry-run is evidence only. Required evidence after a dry-run is the built
artifact names, artifact smoke result, package smoke rehearsal JSON, and
confirmation that no registry upload command ran.

## TestPyPI Publish Rehearsal Checklist - Local Only

This checklist rehearses package publish readiness without publishing a package.
No package registry publish has happened yet. No TestPyPI package URL exists yet.

Credential boundary:

- GitHub prerelease credentials do not authorize TestPyPI or PyPI upload.
- TestPyPI and PyPI credentials are registry-owned release credentials.
- Do not load `.pypirc`, `TWINE_USERNAME`, `TWINE_PASSWORD`,
  `TWINE_API_TOKEN`, or `UV_PUBLISH_TOKEN` for this local-only rehearsal.
- Credential presence is not approval. A human release owner still must set
  `RELEASE_EXECUTION_APPROVED=true` and `PACKAGE_PUBLISH_ALLOWED=true` before
  any upload packet can be run.

Local-only rehearsal commands:

```bash
git status --short -uall
python scripts\worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting
python scripts\alpha_release_gate.py --quick --allow-dirty --json
python -m build --sdist --wheel
python scripts\alpha_release_artifact_smoke.py --with-deps --json
python scripts\package_smoke_rehearsal.py --json --allow-missing-tools
```

`scripts/package_smoke_rehearsal.py` discovers exactly one `dist/*.whl` and the
matching `dist/*.tar.gz` when present. If multiple wheels or sdists exist, pass
`--wheel` and/or `--sdist` with the exact artifact emitted by
`python -m build --sdist --wheel`. The script runs `twine check`, `pipx run
--spec <wheel> qa-z --help`, and `uvx --from <wheel> qa-z --help` only when the
corresponding tool is already available. It does not install global tools.

No-upload guarantee:

- Stop before any registry-specific package upload command.
- Record `registry_upload_executed=false` in the rehearsal notes.
- Record the built artifact names, artifact smoke result, package smoke
  rehearsal result, `twine check` result, `pipx` help smoke result, `uvx` help
  smoke result, and the credential-boundary confirmation.
- Treat package smoke statuses literally: `PASS` means the local command passed,
  `FAIL` means an available local command failed, and `NOT RUN` means the tool
  was unavailable or the check did not execute. Missing tools remain blockers
  for release execution even when `--allow-missing-tools` lets the local
  rehearsal command exit successfully for evidence capture.
- A successful rehearsal proves only local package readiness. It does not prove
  TestPyPI, PyPI, tag, release, or deployment readiness.

Current no-upload tool-smoke evidence:

- `docs/reports/v0.10.0-beta-tool-smoke-execution.md` records
  `scripts/package_smoke_rehearsal.py` passing `twine_check`,
  `pipx_wheel_help`, and `uvx_wheel_help`.
- `registry_upload_executed=false` remains the required package-registry
  boundary.
- This local proof does not authorize any registry upload, tag, GitHub Release,
  deploy, version bump, or registry credential use.

Blocked upload packet:

```bash
python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
```

These upload commands are intentionally blocked until the release owner chooses
the registry, confirms credentials out of band, confirms the pushed SHA has
remote CI and public raw proof, and records the resulting package URL/version.
Rollback is registry-owned: follow the selected registry's yank or retention
policy instead of assuming a local undo command exists.
The v0.10.0-beta rollback/yank policy packet is
`docs/reports/v0.10.0-beta-rollback-yank-policy.md`; it is policy-only, does not
execute rollback/yank actions, and release execution remains `NO-GO`.

## v0.10.0-beta

- Version policy: `docs/reports/v0.10.0-beta-version-policy.md`.
- Package publish path decision:
  `docs/reports/v0.10.0-beta-package-publish-path-decision.md`.
- TestPyPI rehearsal approval:
  `docs/reports/v0.10.0-beta-testpypi-rehearsal-approval.md`.
- TestPyPI rehearsal execution packet:
  `docs/reports/v0.10.0-beta-testpypi-rehearsal-execution-packet.md`.
- TestPyPI rehearsal GO/NO-GO packet:
  `docs/reports/v0.10.0-beta-testpypi-rehearsal-go-no-go.md`.
- Version policy must be decided before package publish.
- The package publish path decision is decision-only, keeps the current
  `No release yet` state, and release execution remains `NO-GO`.
- The TestPyPI rehearsal approval selects TestPyPI rehearsal as the next review
  path, but it does not authorize upload and release execution remains `NO-GO`.
- The TestPyPI rehearsal execution packet prepares pre-upload proof and stop
  rules. It does not upload and release execution remains `NO-GO`.
- The TestPyPI rehearsal GO/NO-GO packet records `NO_GO_MISSING_APPROVAL`;
  it does not upload and release execution remains `NO-GO`.
- Current package metadata remains `0.9.8a0` until a separate approved version
  PR changes `pyproject.toml`.
- No package registry publish is claimed complete.
- The current active install path remains the GitHub source/tag install path
  unless and until package publish happens.
- Future PyPI-published target commands, not current live install claims:

```bash
pipx install qa-z
uv tool install qa-z
```

Do not present these commands as live until PyPI publish is approved, executed,
and proven with the selected package metadata version and package URL.

## Future Installer

The install-script path remains future scope until a stable domain and checksum policy exist:

```bash
curl -LsSf https://qazed.dev/install.sh | sh
```

Do not document this as live until the hosted script, checksum, and rollback policy exist.
