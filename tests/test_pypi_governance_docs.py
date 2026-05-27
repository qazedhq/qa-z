from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE = ROOT / "docs/reports/v0.19-production-pypi-governance.md"
TRUSTED_PUBLISHING = ROOT / "docs/reports/v0.19-pypi-trusted-publishing-design.md"
WORKFLOW_DRAFT = ROOT / "docs/reports/v0.19-pypi-release-workflow-draft.md"
ROLLBACK_PLAYBOOK = ROOT / "docs/reports/v0.19-pypi-rollback-yank-playbook.md"
PACKAGE_PLAN = ROOT / "docs/package-publish-plan.md"
GO_NO_GO = ROOT / "docs/reports/v0.18-production-pypi-go-no-go.md"
READINESS = ROOT / "docs/reports/v0.10.0-beta-pypi-readiness.md"
RELEASE_NOTES = ROOT / "docs/releases/v0.10.0-beta-release-notes-draft.md"
README = ROOT / "README.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(path: Path) -> str:
    return " ".join(read(path).split())


def governance_docs() -> str:
    return "\n".join(
        read(path)
        for path in (
            GOVERNANCE,
            TRUSTED_PUBLISHING,
            WORKFLOW_DRAFT,
            ROLLBACK_PLAYBOOK,
        )
    )


def test_v019_governance_packet_records_blocked_production_pypi_state() -> None:
    assert GOVERNANCE.exists()
    packet = read(GOVERNANCE)

    for required in (
        "v0.19 - Production PyPI Trusted Publishing & Release Governance",
        "Production PyPI status: not published.",
        "Package metadata: `0.10.0b0`.",
        "Current public install: GitHub source tag `v0.9.9-alpha`.",
        "Production PyPI publish remains blocked.",
        "NO_GO_MISSING_APPROVAL",
        "NO_GO_MISSING_CREDENTIALS",
        "fresh final SHA proof",
        "build artifact hashes",
        "`twine check`",
        "production PyPI upload proof",
        "pip/pipx/uv install smoke",
        "README transition proof",
        "rollback/yank stance",
    ):
        assert required in packet


def test_v019_approval_flags_are_documented_without_credential_values() -> None:
    combined = governance_docs()
    combined_lower = combined.lower()

    for required in (
        "`PRODUCTION_PYPI_RELEASE_APPROVED=true`",
        "`PYPI_UPLOAD_ALLOWED=true`",
        "`PACKAGE_PUBLISH_ALLOWED=true`",
        "`TARGET_REGISTRY=PyPI`",
        "`RELEASE_VERSION=0.10.0b0`",
    ):
        assert required in combined

    for forbidden in (
        "pypi-agei",
        "twine_password=",
        "twine_api_token=",
        "pypi_api_token=",
        "uv_publish_token=",
        "credential value:",
        "secret value:",
        "token value:",
    ):
        assert forbidden not in combined_lower


def test_trusted_publishing_design_is_future_only_and_recommended() -> None:
    assert TRUSTED_PUBLISHING.exists()
    design = read(TRUSTED_PUBLISHING)
    design_text = normalized(TRUSTED_PUBLISHING)

    for required in (
        "Manual PyPI API token",
        "PyPI Trusted Publishing via GitHub Actions",
        "Recommended default: PyPI Trusted Publishing via GitHub Actions.",
        "Manual token fallback: explicit fallback only.",
        "GitHub environment name: `pypi-production`.",
        "`id-token: write`",
        "`contents: read`",
        "keep PyPI upload separate from normal CI",
    ):
        assert required in design

    assert (
        "Do not create secrets, configure PyPI trust, or mutate GitHub repository settings from this design."
        in design_text
    )
    assert (
        "Do not log credential values, token material, OIDC token payloads, or registry responses containing secrets."
        in design_text
    )
    assert "future/design-only" in design_text
    assert "twine upload" not in design_text.lower()


def test_release_workflow_draft_is_not_active_publish_workflow() -> None:
    assert WORKFLOW_DRAFT.exists()
    draft = read(WORKFLOW_DRAFT)

    for required in (
        "Draft only - not an active GitHub Actions workflow.",
        "build",
        "twine check",
        "Trusted Publishing publish",
        "pip install smoke",
        "pipx install smoke",
        "uv tool install smoke",
        "README transition PR",
        "Do not copy this into `.github/workflows/` until v0.20",
    ):
        assert required in draft


def test_rollback_yank_playbook_exists_and_keeps_pypi_distinct_from_testpypi() -> None:
    assert ROLLBACK_PLAYBOOK.exists()
    playbook = read(ROLLBACK_PLAYBOOK)
    playbook_lower = playbook.lower()

    for required in (
        "when to yank",
        "when not to delete",
        "who approves",
        "evidence required",
        "post-incident",
        "PyPI production is distinct from TestPyPI",
        "Do not delete a production PyPI release as the default response.",
    ):
        if required.startswith("PyPI") or required.startswith("Do not"):
            assert required in playbook
        else:
            assert required in playbook_lower


def test_current_truth_docs_link_v019_without_claiming_upload() -> None:
    for path in (PACKAGE_PLAN, GO_NO_GO, READINESS, RELEASE_NOTES):
        text = read(path)
        assert "docs/reports/v0.19-production-pypi-governance.md" in text
        assert "No upload occurred in v0.19." in text

    combined_text = " ".join(
        read(path)
        for path in (
            PACKAGE_PLAN,
            GO_NO_GO,
            READINESS,
            RELEASE_NOTES,
            GOVERNANCE,
            TRUSTED_PUBLISHING,
            WORKFLOW_DRAFT,
            ROLLBACK_PLAYBOOK,
        )
    ).lower()
    for false_claim in (
        "production pypi publish completed",
        "pypi upload completed",
        "pypi install is live",
        "live pypi install is available",
        "published to pypi",
        "production_pypi_upload_executed=true",
    ):
        assert false_claim not in combined_text


def test_readme_has_no_live_pypi_install_claim() -> None:
    readme = read(README)

    for forbidden in (
        "pipx install qa-z",
        "uv tool install qa-z",
        "PyPI package available",
        "Install from PyPI",
    ):
        assert forbidden not in readme


def test_pr89_pr90_superseded_cleanup_is_not_documented_without_closure() -> None:
    combined = governance_docs()

    assert "#89" not in combined
    assert "#90" not in combined
    assert "Closing as superseded" not in combined
