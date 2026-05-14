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
python -m twine check dist/*
```

The dry-run is evidence only. Required evidence after a dry-run is the built
artifact names, artifact smoke result, `twine check` result, and confirmation
that no registry upload command ran.

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
