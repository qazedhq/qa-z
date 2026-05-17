from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = "docs/reports/v0.10.0-beta-rollback-yank-policy.md"
POLICY = ROOT / POLICY_PATH


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_rollback_yank_policy_exists_and_keeps_beta_unreleased() -> None:
    assert POLICY.exists()
    policy = read(POLICY)

    for section in (
        "## Purpose",
        "## Current Non-release State",
        "## Policy Scope",
        "## Registry / Release Path Matrix",
        "## Required Decision Fields",
        "## What Local Rollback Cannot Prove",
        "## Blocked Actions",
        "## Incident / Communication Steps",
        "## Required Proof Before Execution",
        "## Recommended Current Decision",
        "## Explicit Non-actions",
    ):
        assert section in policy

    assert "This is policy-only." in policy
    assert "`v0.10.0-beta` is not released." in policy
    assert "Release execution remains `NO-GO`." in policy
    assert "Current public alpha remains `v0.9.9-alpha`." in policy
    assert "Current package metadata remains `0.9.8a0`." in policy


def test_rollback_yank_policy_covers_release_paths_separately() -> None:
    policy = read(POLICY)

    for release_path in (
        "No release yet",
        "GitHub prerelease only",
        "TestPyPI publish",
        "PyPI publish",
        "npm publish",
        "GitHub Packages publish",
        "docs site / hosted demo deploy",
        "metadata-only version PR",
    ):
        assert release_path in policy

    for matrix_column in (
        "Rollback/yank concern",
        "Required owner decision",
        "Required official-policy check",
        "Required proof",
        "Blocked action",
        "Current status",
    ):
        assert matrix_column in policy


def test_rollback_yank_policy_requires_official_policy_checks() -> None:
    policy = read(POLICY)

    for source in (
        "https://docs.pypi.org/project-management/yanking/",
        "https://docs.npmjs.com/policies/unpublish/",
        "https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository",
        "https://docs.github.com/en/rest/git/refs",
        "https://docs.github.com/en/packages/learn-github-packages/deleting-and-restoring-a-package",
    ):
        assert source in policy

    assert "Registry-specific official docs must be checked before execution." in (
        policy
    )
    assert "deploy platform rollback policy" in policy
    assert "official policy checked at execution time" in policy


def test_rollback_yank_policy_blocks_actions_and_local_undo_claims() -> None:
    policy = read(POLICY)
    text = normalized(policy)

    assert (
        "Local git revert or local artifact deletion does not prove registry rollback."
        in policy
    )
    assert "local undo command exists" not in policy

    for blocked_action in (
        "tag deletion",
        "GitHub Release deletion",
        "package publish",
        "package yank",
        "package delete",
        "deploy",
        "version bump",
        "twine upload",
    ):
        assert blocked_action in policy

    assert (
        "No tag, GitHub Release, package publish, yank, delete, deploy, or version bump is authorized."
        in text
    )

    for false_claim in (
        "v0.10.0-beta is released",
        "release execution is `GO`",
        "PyPI publish completed",
        "TestPyPI publish completed",
        "registry_upload_executed=true",
        "rollback/yank policy is approved",
    ):
        assert false_claim not in policy


def test_rollback_yank_policy_preserves_approval_and_blockers() -> None:
    policy = read(POLICY)

    for required in (
        "release-owner approval",
        "credentials are not approval",
        "Rollback/yank policy remains `BLOCKED` until release-owner approval.",
        "tool-equipped twine/pipx/uvx smoke remains `NOT RUN`",
        "Next.js/PostCSS advisory option/proof remains `BLOCKED`",
        "registry credentials remain `BLOCKED`",
        "version/package metadata execution decision remains `BLOCKED`",
        "final release-execution-time SHA proof remains `BLOCKED`",
    ):
        assert required in policy


def test_existing_release_docs_link_rollback_yank_policy() -> None:
    for report_path in (
        "docs/reports/v0.10.0-beta-release-execution-checklist.md",
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
        "docs/package-publish-plan.md",
    ):
        report = read(report_path)
        text = normalized(report)
        assert POLICY_PATH in report
        assert (
            "release execution remains `NO-GO`" in text
            or "Release execution remains `NO-GO`" in text
        )
        assert "rollback/yank" in text
