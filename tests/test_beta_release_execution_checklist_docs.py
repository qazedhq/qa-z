from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CHECKLIST_PATH = "docs/reports/v0.10.0-beta-release-execution-checklist.md"
CHECKLIST = ROOT / CHECKLIST_PATH
FINAL_PROTOCOL_PATH = "docs/reports/v0.10.0-beta-final-sha-proof-protocol.md"


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_release_execution_checklist_exists_and_does_not_release_beta() -> None:
    assert CHECKLIST.exists()
    checklist = read(CHECKLIST)

    for section in (
        "## Purpose",
        "## Current Non-release State",
        "## Required Approval Fields",
        "## Pre-execution Gate Order",
        "## GO / NO-GO Status Matrix",
        "## Required Proof Links",
        "## Blocked Actions",
        "## Execution-time Final SHA Proof",
        "## Package Publish Boundary",
        "## Rollback / Yank Policy",
        "## Explicit Non-actions",
        "## Recommended Current Decision",
    ):
        assert section in checklist

    assert "This checklist does not execute a release." in checklist
    assert "`v0.10.0-beta` is not released." in checklist
    assert "Current public alpha remains `v0.9.9-alpha`." in checklist
    assert "Current package metadata remains `0.9.8a0`." in checklist
    assert "Release execution is currently `NO-GO`." in checklist


def test_release_execution_checklist_records_required_approval_fields() -> None:
    checklist = read(CHECKLIST)

    for approval_field in (
        "RELEASE_EXECUTION_APPROVED",
        "PACKAGE_PUBLISH_ALLOWED",
        "release owner",
        "release type",
        "target tag",
        "target package metadata version",
        "target registry",
        "exact release SHA",
        "remote CI proof link",
        "public raw proof link",
        "package smoke proof link",
        "advisory decision proof link",
        "rollback/yank policy link",
    ):
        assert approval_field in checklist


def test_release_execution_checklist_status_matrix_has_required_gates() -> None:
    checklist = read(CHECKLIST)

    for status in (
        "`PASS`",
        "`FAIL`",
        "`BLOCKED`",
        "`NOT RUN`",
        "`NO-GO`",
        "`APPROVED`",
        "`NOT APPROVED`",
    ):
        assert status in checklist

    for gate in (
        "release-owner approval",
        "version/package metadata execution decision",
        "final release-execution-time SHA proof",
        "CI proof",
        "Public Raw Hygiene proof",
        "public raw file proof",
        "tool-equipped twine/pipx/uvx smoke",
        "Next.js/PostCSS advisory option/proof",
        "registry credentials",
        "rollback/yank policy",
        "generated artifact cleanup",
        "release notes/tag policy",
        "package publish authorization",
    ):
        assert gate in checklist

    for current_state in (
        "| release-owner approval | `NOT APPROVED` |",
        "| tool-equipped twine/pipx/uvx smoke | `PASS` |",
        "| Next.js/PostCSS advisory option/proof | `BLOCKED` |",
        "| registry credentials | `BLOCKED` |",
        "| version/package metadata execution decision | `BLOCKED` |",
        "| final release-execution-time SHA proof | `BLOCKED` |",
        "| rollback/yank policy | `BLOCKED` |",
    ):
        assert current_state in checklist


def test_release_execution_checklist_blocks_release_actions() -> None:
    checklist = read(CHECKLIST)
    text = normalized(checklist)

    for blocked in (
        "No tag",
        "GitHub Release",
        "package publish",
        "deploy",
        "version bump",
        "twine upload",
    ):
        assert blocked in checklist

    assert "No tag, GitHub Release, package publish, deploy, or version bump" in text
    assert "not authorized by this checklist" in text

    for false_claim in (
        "v0.10.0-beta is released",
        "release execution is `GO`",
        "PyPI publish completed",
        "TestPyPI publish completed",
        "registry_upload_executed=true",
    ):
        assert false_claim not in checklist


def test_release_execution_checklist_links_proofs_and_preserves_blockers() -> None:
    checklist = read(CHECKLIST)

    for link in (
        "docs/reports/v0.10.0-beta-readiness.md",
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
        "docs/reports/v0.10.0-beta-tool-smoke-execution.md",
        "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md",
        "docs/reports/v0.10.0-beta-exact-sha-proof.md",
        FINAL_PROTOCOL_PATH,
        "docs/package-publish-plan.md",
    ):
        assert link in checklist

    for blocker in (
        "Final SHA proof must be generated after release-candidate SHA freeze.",
        "Tool-equipped twine/pipx/uvx smoke is satisfied as local no-upload evidence",
        "Next.js/PostCSS advisory option/proof is separate and still required.",
        "Registry credentials and rollback/yank policy are separate and still required.",
    ):
        assert blocker in checklist


def test_existing_beta_reports_link_release_execution_checklist() -> None:
    for report_path in (
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-readiness.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
        "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md",
        "docs/reports/v0.10.0-beta-final-sha-proof-protocol.md",
    ):
        report = read(report_path)
        text = normalized(report)
        assert CHECKLIST_PATH in report
        assert "checklist does not execute release" in text
        assert (
            "release execution `NO-GO`" in text
            or "release execution remains `NO-GO`" in text
        )
