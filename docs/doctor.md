# Doctor diagnostics

Run `qa-z doctor` before the first guard run in a new repository, after
installing a wheel or sdist, inside a source checkout, or when a GitHub Actions
job fails before useful QA-Z evidence appears.

Doctor is a local diagnostic command. It does not upload to PyPI or TestPyPI,
create tags, create GitHub Releases, deploy, post comments, or mutate target
repositories.

## Statuses

`qa-z doctor` reports one overall status:

- `passed`: required local diagnostics are usable.
- `warning`: QA-Z can continue, but a setup problem may limit the next command.
- `failed`: a local contract is broken enough that QA-Z commands may not write
  evidence or load required resources.

The human output is intentionally short:

```text
QA-Z Doctor: warning
qa-z doctor: warning

PASS package version: 0.10.0b0
PASS python: 3.11.9
WARN qa-z.yaml: missing
PASS templates: auth-bug demo resources found
WARN semgrep: not found; deep checks may be limited

Next actions:
1. Run `qa-z init`.
2. Run `qa-z demo auth-bug`.
3. Install Semgrep if you want deep checks.
```

Use `qa-z doctor --json` when automation needs stable fields. The top-level
JSON fields are `status`, `version`, `checks`, `warnings`, `errors`,
`suggestions`, and `next_actions`. Each check includes `id`, `status`,
`message`, `evidence`, and `suggestion`.

## What doctor checks

Runtime diagnostics include Python version, executable path, platform, package
version, module path, and invocation path.

Install diagnostics identify available hints for editable installs, source
checkout imports, wheel/sdist installs, pipx-like paths, virtual environments,
GitHub Actions, or unknown environments. A source checkout can report both
`source checkout` and `venv` when QA-Z is imported from `src/qa_z` inside a
virtual environment.

Project diagnostics check the selected project root, git availability, whether
the root is inside a git repository, `qa-z.yaml` presence, profile shape, and
configured fast/deep check counts. If `qa-z.yaml` is missing, run `qa-z init`.

Tool diagnostics check `git` and Semgrep. Missing Semgrep is a warning because
fast checks and config validation can still run, but deep checks may be
limited.

Resource diagnostics verify packaged auth-bug demo resources are loadable from
package data. This matters for installed package smoke because the demo should
work from a wheel or sdist, not only from a source tree.

Runtime artifact diagnostics create and remove a temporary marker under the
`.qa-z` runtime directory. If this fails, fix directory permissions or run from
a writable project path before expecting guard, review, repair, or verify
artifacts.

GitHub Actions diagnostics detect `GITHUB_ACTIONS=true` and
`GITHUB_STEP_SUMMARY`. SARIF and pull request comments are action-level opt-ins;
doctor reports the environment, but it does not grant permissions or enable
uploads/comments.

## Common fixes

- Missing `qa-z.yaml`: run `qa-z init` or pass `--config` to an existing config.
- Missing Semgrep: install Semgrep when you want deep checks.
- Missing auth-bug resources: reinstall QA-Z from the source checkout or
  package artifact.
- `.qa-z` not writable: fix permissions, remove a stale file blocking the
  directory, or run from a writable checkout.
- GitHub Actions summary missing: verify the job environment and inspect the
  workflow step that runs QA-Z.

## Package boundary

Production PyPI is not published. The current public install path remains the
GitHub source/tag install path until a separate release-owner package publish
packet is approved and executed.

`qa-z doctor` may run from installed package smoke, source checkout smoke,
GitHub Actions, or local venv/pipx-like environments, but it does not claim live
PyPI install availability.
