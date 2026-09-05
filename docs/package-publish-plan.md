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
Current release proof HEAD: `ab98055ede02bda0377b403ab20d12ffa4863c87`.

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
python -m twine check dist/*
```

The dry-run is evidence only. Required evidence after a dry-run is the built
artifact names, artifact smoke result, `twine check` result, and confirmation
that no registry upload command ran.

## TestPyPI Publish Rehearsal - 2026-05-23

Package metadata version: `0.9.8a0`.
Target registry: TestPyPI only.
Package URL: `https://test.pypi.org/project/qa-z/0.9.8a0/`.

Approved release-owner fields for this rehearsal:

- `RELEASE_EXECUTION_APPROVED=true`
- `PACKAGE_PUBLISH_ALLOWED=true`
- `TESTPYPI_UPLOAD_ALLOWED=true`
- `PYPI_UPLOAD_ALLOWED=false`
- `SELECTED_RELEASE_PATH=TestPyPI rehearsal only`
- `TARGET_REGISTRY=TestPyPI`
- `REGISTRY_UPLOAD_SCOPE=TestPyPI only`

Executed artifacts:

- `dist/qa_z-0.9.8a0.tar.gz`
- `dist/qa_z-0.9.8a0-py3-none-any.whl`

Validation and upload evidence:

- `python scripts\alpha_release_gate.py --quick --allow-dirty --json`: passed.
- `python -m build --sdist --wheel`: built the exact sdist and wheel above.
- `python scripts\alpha_release_artifact_smoke.py --with-deps --json`: passed.
- `python scripts\package_smoke_rehearsal.py --json` in an isolated tool
  environment with `twine`, `pipx`, and `uvx`: passed with
  `registry_upload_executed=false`.
- `twine check` on the exact sdist and wheel: passed.
- `twine upload --repository-url https://test.pypi.org/legacy/` on the exact
  sdist and wheel: completed.
- TestPyPI simple index with prereleases enabled lists `qa-z (0.9.8a0)`.
- A fresh virtual environment installed `qa-z==0.9.8a0` from TestPyPI with PyPI
  as dependency fallback and ran `python -m qa_z --help`.

Explicit non-actions:

- No PyPI upload ran.
- No tag was created.
- No GitHub Release was created.
- No deploy ran.
- No version metadata changed.
- Do not use `dist/*` for future uploads; `dist/` can contain non-package
  bundle artifacts. Use exact sdist and wheel paths.

## TestPyPI Publish Rehearsal Checklist - Historical Local-Only Baseline

This checklist rehearsed package publish readiness without publishing a package.
It is kept as the local-only baseline that preceded the 2026-05-23 TestPyPI
upload rehearsal recorded above.

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
python -m twine check dist/*
pipx run --spec dist/qa_z-0.9.8a0-py3-none-any.whl qa-z --help
uvx --from dist/qa_z-0.9.8a0-py3-none-any.whl qa-z --help
```

If package metadata changes, replace the wheel filename with the exact wheel
emitted by `python -m build --sdist --wheel`.

No-upload guarantee:

- Stop before any `twine upload`, `uv publish`, or registry-specific upload
  command.
- Record `registry_upload_executed=false` in the rehearsal notes.
- Record the built artifact names, artifact smoke result, package smoke
  rehearsal JSON, `twine check` result, `pipx` help smoke result, `uvx` help
  smoke result, and the credential-boundary confirmation.
- Missing `twine`, `pipx`, or `uvx` tools in the scripted rehearsal must be
  recorded as `NOT_RUN`, not `PASS`.
- A successful rehearsal proves only local package readiness. It does not prove
  TestPyPI, PyPI, tag, release, or deployment readiness.

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

## v0.10.0-beta

- PyPI publish.
- Front-page install:

```bash
pipx install qa-z
uv tool install qa-z
```

## Future Installer

The install-script path remains future scope until a stable domain and checksum policy exist:

```bash
curl -LsSf https://qazed.dev/install.sh | sh
```

Do not document this as live until the hosted script, checksum, and rollback policy exist.
