from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_POLICY = ROOT / "docs/reports/v0.10.0-beta-version-policy.md"


def read(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_beta_version_policy_doc_exists_and_keeps_beta_unreleased() -> None:
    assert VERSION_POLICY.exists()
    policy = read(VERSION_POLICY)

    assert "This policy does not release `v0.10.0-beta`." in policy
    assert "`v0.10.0-beta` remains planned, not released." in policy
    assert "`v0.9.9-alpha` GitHub prerelease" in policy
    assert "`0.9.8a0` in `pyproject.toml`" in policy
    assert "Current package metadata" in policy

    for false_claim in (
        "v0.10.0-beta is released",
        "PyPI publish completed",
        "TestPyPI publish completed",
        "registry_upload_executed=true",
    ):
        assert false_claim not in policy


def test_beta_version_policy_keeps_pyproject_metadata_current() -> None:
    pyproject = read(ROOT / "pyproject.toml")
    match = re.search(r'^version = "([^"]+)"$', pyproject, flags=re.MULTILINE)

    assert match is not None
    assert match.group(1) == "0.9.8a0"

    policy = read(VERSION_POLICY)
    assert '`pyproject.toml` remains at `version = "0.9.8a0"`.' in policy
    assert (
        "`0.10.0b0` is a candidate package metadata version, not current metadata."
        in policy
    )
    assert "Candidate only, not current metadata" in policy
    assert "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md" in policy
    assert "docs/reports/v0.10.0-beta-final-sha-proof-protocol.md" in policy
    assert "release execution `NO-GO` remains unchanged" in policy


def test_beta_version_policy_links_from_release_decision_packet() -> None:
    decision_packet = read(ROOT / "docs/reports/v0.10.0-beta-release-decision.md")
    normalized = " ".join(decision_packet.split())

    assert "docs/reports/v0.10.0-beta-version-policy.md" in decision_packet
    assert "does not change `pyproject.toml`" in normalized
    assert "not release execution" in normalized


def test_package_publish_plan_marks_pipx_and_uv_as_future_pypi_targets() -> None:
    package_plan = read(ROOT / "docs/package-publish-plan.md")
    beta_section = package_plan.split("## v0.10.0-beta", 1)[1]
    normalized = " ".join(beta_section.split())

    assert "docs/reports/v0.10.0-beta-version-policy.md" in beta_section
    assert "Future PyPI-published target commands" in normalized
    assert "not current live install claims" in normalized
    assert "pipx install qa-z" in beta_section
    assert "uv tool install qa-z" in beta_section
    assert (
        "current active install path remains the GitHub source/tag install path"
        in normalized
    )
    assert "TestPyPI rehearsal upload is complete" in beta_section
    assert "registry_upload_executed=true applies to TestPyPI only" in beta_section
    assert (
        "No production PyPI package registry publish is claimed complete"
        in beta_section
    )


def test_beta_version_policy_blocks_release_execution_without_approval() -> None:
    policy = read(VERSION_POLICY)

    for blocked_action in (
        "changing `pyproject.toml` version without release-owner approval",
        "creating a tag",
        "creating a GitHub Release",
        "publishing to PyPI, TestPyPI, npm, GitHub Packages, or any package registry",
        "deploying a docs site or hosted demo",
        "`twine`, `pipx`, or `uvx` smoke passed without fresh evidence",
        "hiding the Next.js/PostCSS advisory blocker",
    ):
        assert blocked_action in policy

    for approval_field in (
        "RELEASE_EXECUTION_APPROVED=true",
        "PACKAGE_PUBLISH_ALLOWED=true",
        "target package metadata version",
        "remote CI proof SHA",
        "public raw proof SHA",
        "rollback/yank policy",
    ):
        assert approval_field in policy
