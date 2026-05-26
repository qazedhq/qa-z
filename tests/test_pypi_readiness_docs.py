from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "docs/reports/v0.10.0-beta-pypi-readiness.md"
PUBLISHING_METHOD = ROOT / "docs/reports/v0.10.0-beta-pypi-publishing-method.md"
README_TRANSITION = ROOT / "docs/reports/v0.10.0-beta-readme-install-transition.md"
SMOKE_PLAN = ROOT / "docs/reports/v0.10.0-beta-pypi-install-smoke-plan.md"
INSTALLED_PACKAGE_SMOKE = ROOT / "docs/reports/v0.10.0-beta-installed-package-smoke.md"
PRODUCTION_GO_NO_GO = ROOT / "docs/reports/v0.18-production-pypi-go-no-go.md"
RELEASE_NOTES_DRAFT = ROOT / "docs/releases/v0.10.0-beta-release-notes-draft.md"
VERSION_POLICY = ROOT / "docs/reports/v0.10.0-beta-version-policy.md"
LAUNCH_KIT = ROOT / "docs/launch/launch-kit.md"
PACKAGE_PUBLISH_PLAN = ROOT / "docs/package-publish-plan.md"
README = ROOT / "README.md"
PYPROJECT = ROOT / "pyproject.toml"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(path: Path) -> str:
    return " ".join(read(path).split())


def pyproject_version() -> str:
    match = re.search(
        r'^version = "([^"]+)"$',
        read(PYPROJECT),
        flags=re.MULTILINE,
    )
    assert match is not None
    return match.group(1)


def test_pypi_readiness_summary_records_testpypi_only_truth() -> None:
    assert READINESS.exists()
    readiness = read(READINESS)
    readiness_text = normalized(READINESS)

    for required in (
        "TestPyPI rehearsal completed.",
        "https://test.pypi.org/project/qa-z/0.9.8a0/",
        "Production PyPI has not been published.",
        "Current source metadata: `qa-z` / `0.10.0b0`.",
        "Historical TestPyPI proof remains `qa-z==0.9.8a0`.",
        "Owner-approved package metadata version: `0.10.0b0`.",
        "`registry_upload_executed=true` applies to TestPyPI `0.9.8a0` only.",
        "Report: `docs/reports/v0.10.0-beta-installed-package-smoke.md`.",
        "`python scripts/installed_package_smoke.py --json`: passed locally.",
        "Both artifact forms installed into fresh virtual environments.",
        "`registry_upload_executed=false`; no PyPI/TestPyPI upload",
        "Required gates before PyPI publish",
        "Explicit non-actions",
    ):
        assert required in readiness

    for blocked_action in (
        "No production PyPI upload occurred in this PR.",
        "No `twine upload` command ran in this PR.",
        "No tag or GitHub Release was created.",
        "No deploy occurred.",
        "No package publish occurred; the `pyproject.toml` change is metadata-only.",
        "No live PyPI install is claimed.",
    ):
        assert blocked_action in readiness

    assert "PyPI upload completed" not in readiness_text
    assert "live `pipx install qa-z`" not in readiness_text
    assert "live `uv tool install qa-z`" not in readiness_text
    assert pyproject_version() == "0.10.0b0"


def test_installed_package_smoke_report_records_local_runtime_proof_only() -> None:
    assert INSTALLED_PACKAGE_SMOKE.exists()
    report = read(INSTALLED_PACKAGE_SMOKE)
    report_text = normalized(INSTALLED_PACKAGE_SMOKE)
    package_plan = read(PACKAGE_PUBLISH_PLAN)

    for required in (
        "Status: local installed-package runtime smoke passed.",
        "Source metadata under test: `qa-z` / `0.10.0b0`.",
        "Summary: `installed package smoke passed`.",
        "`registry_upload_executed=false`.",
        "Wheel artifact smoke: `PASS`.",
        "Sdist artifact smoke: `PASS`.",
        "Run `qa-z --help`.",
        "Run `python -m qa_z --help`.",
        "Run `qa-z demo auth-bug --json`.",
        "Run `qa-z doctor --json --path <demo-root> --config qa-z.demo.yaml`.",
        "Run `qa-z guard --from-run latest --adapter codex`.",
        "Run `qa-z repair-prompt --from-run latest --adapter codex`.",
        "Copy `app/auth.fixed.py` over `app/auth.py`.",
        "Run `qa-z verify --from-run latest --json`.",
        "Demo resource loading passed from both installed artifact forms.",
        "No production PyPI upload occurred.",
        "No TestPyPI upload occurred.",
        "No live `pipx install qa-z` or `uv tool install qa-z` claim is made.",
    ):
        assert required in report

    assert "PyPI publish completed" not in report_text
    assert "registry_upload_executed=true" not in report_text
    assert "v0.10.0-beta-installed-package-smoke.md" in package_plan
    assert "Local installed-package smoke passed" in package_plan


def test_v018_production_pypi_go_no_go_packet_records_blocked_upload() -> None:
    assert PRODUCTION_GO_NO_GO.exists()
    packet = read(PRODUCTION_GO_NO_GO)
    packet_text = normalized(PRODUCTION_GO_NO_GO)
    package_plan = read(PACKAGE_PUBLISH_PLAN)
    readiness = read(READINESS)
    release_notes = read(RELEASE_NOTES_DRAFT)
    readme = read(README)

    for required in (
        "Decision: `NO_GO_MISSING_APPROVAL`",
        "Secondary decision: `NO_GO_MISSING_CREDENTIALS`",
        "Release version: `0.10.0b0`",
        "Final release SHA frozen: no.",
        "Local readiness source SHA checked:",
        "`202e4b0c84439578694997db63492546ccb5e27e`",
        "`PRODUCTION_PYPI_RELEASE_APPROVED` | `true` | missing",
        "`PYPI_UPLOAD_ALLOWED` | `true` | missing",
        "`PACKAGE_PUBLISH_ALLOWED` | `true` | missing",
        "`TARGET_REGISTRY` | `PyPI` | missing",
        "`RELEASE_VERSION` | `0.10.0b0` | missing",
        "`python -m pip index versions qa-z`: `ERROR: No matching distribution found for qa-z`.",
        "`https://pypi.org/simple/qa-z/`: HTTP 404.",
        "Production PyPI package proof for `qa-z==0.10.0b0` does not exist",
        "`python -m build --sdist --wheel` | passed",
        "`python scripts/installed_package_smoke.py --json` | passed",
        "`dist/qa_z-0.10.0b0-py3-none-any.whl` | 389786",
        "`303148adc5287c74afb53c33c708531b79da3635a9667a14b039ad6f98e054a0`",
        "`dist/qa_z-0.10.0b0.tar.gz` | 582485",
        "`47d76fbc193e60e0d6539832ac552a3dfd430d0f4bc98b75ad6c4d7cb0791e94`",
        '`"summary": "installed package smoke passed"`',
        '`"registry_upload_executed": false`',
        "README transition status: unchanged.",
        "`production_pypi_upload_executed=false`",
        "`registry_upload_executed=false` for production PyPI",
    ):
        assert required in packet

    for linked_surface in (package_plan, readiness, release_notes):
        assert "v0.18-production-pypi-go-no-go.md" in linked_surface
        assert "NO_GO_MISSING_APPROVAL" in linked_surface

    assert "NO_GO_MISSING_CREDENTIALS" in package_plan
    assert "Production PyPI upload remains blocked." in package_plan
    assert "pipx install qa-z" not in readme
    assert "uv tool install qa-z" not in readme

    for false_claim in (
        "GO_FOR_PRODUCTION_PYPI_UPLOAD` | selected",
        "production_pypi_upload_executed=true",
        "registry_upload_executed=true for production",
        "PyPI upload completed",
        "PyPI install is live",
        "live PyPI install is available",
    ):
        assert false_claim not in packet_text


def test_version_policy_records_testpypi_rehearsal_and_candidate_only() -> None:
    policy = read(VERSION_POLICY)

    for required in (
        "`0.9.8a0` was used for the TestPyPI rehearsal.",
        "`0.10.0b0` is the current source metadata after this PR.",
        "Production PyPI publish remains blocked.",
        "Future version bumps require separate owner approval and a separate PR.",
    ):
        assert required in policy

    assert "Current source metadata after this metadata-only PR" in policy
    assert pyproject_version() == "0.10.0b0"


def test_pypi_publishing_method_decision_keeps_upload_blocked() -> None:
    assert PUBLISHING_METHOD.exists()
    method = read(PUBLISHING_METHOD)
    method_text = normalized(PUBLISHING_METHOD)

    for required in (
        "Manual PyPI API token",
        "PyPI Trusted Publishing via GitHub Actions",
        "Approval requirements",
        "Credential boundaries",
        "GitHub permission implications",
        "Recommended path",
        "No upload in this PR",
    ):
        assert required in method

    assert "Recommended path: PyPI Trusted Publishing via GitHub Actions." in method
    assert "production PyPI publish remains blocked" in method_text
    assert "manual token value" not in method_text.lower()
    assert "twine upload" not in method_text.lower()


def test_readme_install_transition_plan_requires_live_pypi_proof() -> None:
    assert README_TRANSITION.exists()
    transition = read(README_TRANSITION)

    for required in (
        "Current GitHub source install",
        "Future PyPI install target",
        "Exact conditions before README can switch",
        "Tests that must pass before switching",
        "No live PyPI claim yet",
        "pipx install git+https://github.com/qazedhq/qa-z.git",
    ):
        assert required in transition

    for required_test in (
        "python -m pytest tests/test_pypi_readiness_docs.py -q",
        "python -m pytest tests/test_public_docs_current_truth.py tests/test_launch_growth_package.py tests/test_beta_version_policy_docs.py -q",
        "python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public",
        "python -m qa_z --help",
    ):
        assert required_test in transition

    readme = read(README)
    assert "pipx install qa-z" not in readme
    assert "uv tool install qa-z" not in readme


def test_pypi_install_smoke_plan_marks_commands_future_only() -> None:
    assert SMOKE_PLAN.exists()
    smoke = read(SMOKE_PLAN)
    smoke_text = normalized(SMOKE_PLAN)

    assert "Future commands after PyPI publish only." in smoke
    for command in (
        "python -m pip install qa-z==0.10.0b0",
        "pipx install qa-z==0.10.0b0",
        "uv tool install qa-z==0.10.0b0",
        "qa-z demo auth-bug",
    ):
        assert command in smoke

    assert "Do not run these commands before production PyPI publish" in smoke
    assert "not current live install commands" in smoke_text


def test_release_notes_draft_has_no_release_execution_claim() -> None:
    assert RELEASE_NOTES_DRAFT.exists()
    release_notes = read(RELEASE_NOTES_DRAFT)
    release_text = normalized(RELEASE_NOTES_DRAFT)

    for section in (
        "## Summary",
        "## Key Improvements Since v0.9.9-alpha",
        "## TestPyPI Proof",
        "## Install Status",
        "## Known Limitations",
        "## Release Boundary",
    ):
        assert section in release_notes

    for required in (
        "Draft only - not a GitHub Release.",
        "TestPyPI proof exists at https://test.pypi.org/project/qa-z/0.9.8a0/",
        "Production PyPI is not published.",
        "GitHub source install remains the current public install path.",
        "`v0.10.0-beta` is not released.",
    ):
        assert required in release_notes

    for false_claim in (
        "GitHub Release created",
        "tag created",
        "deployed",
        "version bumped",
        "PyPI publish completed",
        "live PyPI install",
    ):
        assert false_claim not in release_text


def test_launch_kit_reflects_testpypi_completed_but_pypi_future() -> None:
    launch_kit = read(LAUNCH_KIT)

    for required in (
        "TestPyPI rehearsal completed.",
        "Production PyPI is not live.",
        "PyPI install remains future.",
        "GitHub source install remains the current public install path.",
    ):
        assert required in launch_kit
