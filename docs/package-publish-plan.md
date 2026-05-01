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

- TestPyPI publish rehearsal.
- `pipx` install from Git tag smoke.
- `uv tool install` from Git tag smoke.
- Release artifact smoke using `python scripts/alpha_release_artifact_smoke.py --with-deps --json`.

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
