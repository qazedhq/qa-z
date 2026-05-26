from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "docs/reports/v0.10.0-beta-pypi-readiness.md"
PUBLISHING_METHOD = ROOT / "docs/reports/v0.10.0-beta-pypi-publishing-method.md"
README_TRANSITION = ROOT / "docs/reports/v0.10.0-beta-readme-install-transition.md"
SMOKE_PLAN = ROOT / "docs/reports/v0.10.0-beta-pypi-install-smoke-plan.md"
RELEASE_NOTES_DRAFT = ROOT / "docs/releases/v0.10.0-beta-release-notes-draft.md"
VERSION_POLICY = ROOT / "docs/reports/v0.10.0-beta-version-policy.md"
LAUNCH_KIT = ROOT / "docs/launch/launch-kit.md"
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
        "Current metadata: `qa-z` / `0.9.8a0`.",
        "Recommended candidate version: `0.10.0b0`, pending owner decision.",
        "`registry_upload_executed=true` applies to TestPyPI only.",
        "Required gates before PyPI publish",
        "Explicit non-actions",
    ):
        assert required in readiness

    for blocked_action in (
        "No production PyPI upload occurred in this PR.",
        "No `twine upload` command ran in this PR.",
        "No tag or GitHub Release was created.",
        "No deploy occurred.",
        "No `pyproject.toml` version bump occurred.",
        "No live PyPI install is claimed.",
    ):
        assert blocked_action in readiness

    assert "PyPI upload completed" not in readiness_text
    assert "live `pipx install qa-z`" not in readiness_text
    assert "live `uv tool install qa-z`" not in readiness_text
    assert pyproject_version() == "0.9.8a0"


def test_version_policy_records_testpypi_rehearsal_and_candidate_only() -> None:
    policy = read(VERSION_POLICY)

    for required in (
        "`0.9.8a0` was used for the TestPyPI rehearsal.",
        "`0.10.0b0` is the recommended production PyPI beta candidate.",
        "`pyproject.toml` is not changed in this PR.",
        "The version bump requires separate owner approval and a separate PR.",
    ):
        assert required in policy

    assert "Candidate only, not current metadata" in policy
    assert pyproject_version() == "0.9.8a0"


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
