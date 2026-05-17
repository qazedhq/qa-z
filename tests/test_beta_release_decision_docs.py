from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION_PACKET = ROOT / "docs/reports/v0.10.0-beta-release-decision.md"


def read_packet() -> str:
    return DECISION_PACKET.read_text(encoding="utf-8")


def test_beta_release_decision_packet_exists_and_blocks_release_claims() -> None:
    assert DECISION_PACKET.exists()
    packet = read_packet()

    assert "This packet is not a release execution record." in packet
    assert "`v0.10.0-beta` is not released by\nthis packet" in packet
    assert "No package registry upload has been run." in packet
    assert "No tag has been created by\nthis packet." in packet
    assert "No GitHub Release has been created by this packet." in packet
    assert "No deploy has\nbeen performed by this packet." in packet
    assert "Current public alpha remains `v0.9.9-alpha`" in packet
    assert "package metadata remains `0.9.8a0`" in packet

    for false_claim in (
        "PyPI publish completed",
        "TestPyPI publish completed",
        "registry_upload_executed=true",
        "v0.10.0-beta is released",
    ):
        assert false_claim not in packet


def test_beta_release_decision_lists_all_release_path_options() -> None:
    packet = read_packet()

    for option in (
        "No release yet",
        "GitHub prerelease only",
        "TestPyPI rehearsal only",
        "TestPyPI publish",
        "PyPI publish",
        "Version metadata bump only",
    ):
        assert option in packet


def test_beta_release_decision_records_required_approval_fields() -> None:
    packet = read_packet()

    for approval_field in (
        "RELEASE_EXECUTION_APPROVED",
        "PACKAGE_PUBLISH_ALLOWED",
        "target tag",
        "target package metadata version",
        "target registry",
        "release type",
        "release owner",
        "rollback/yank policy",
        "external proof links",
        "remote CI proof SHA",
        "public raw proof SHA",
    ):
        assert approval_field in packet


def test_beta_release_decision_blocks_upload_tag_release_commands() -> None:
    packet = read_packet()

    assert "These examples are blocked commands, not safe commands." in packet
    for blocked_command in (
        "python -m twine upload --repository testpypi dist/*",
        "python -m twine upload dist/*",
        "git tag ...",
        "gh release create ...",
        "npm publish",
        "deploy commands",
    ):
        assert blocked_command in packet

    assert "`twine upload`, `uv publish`, npm registry publish" in packet
    assert "not part of this packet" in packet


def test_beta_release_decision_records_package_smoke_proof_and_advisory_blockers() -> (
    None
):
    packet = read_packet()

    assert "scripts/package_smoke_rehearsal.py" in packet
    assert "`PASS`/`FAIL`/`NOT RUN` statuses" in packet
    for blocker in (
        "Tool-equipped package smoke rehearsal",
        "`twine_check`, `pipx_wheel_help`, and `uvx_wheel_help` as `PASS`",
        "registry_upload_executed=false",
        "Next.js npm moderate advisories",
        "no automatic dependency fix is implied",
        "GHSA-qx2v-qp2m-jg93",
        "CVE-2026-41305",
        "next@15.5.18",
        "postcss@8.4.31",
        "PostCSS is patched at `8.5.10`",
        "next@latest",
        "do not run `npm audit fix --force`",
        "downgrade Next.js",
        "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md",
        "release execution `NO-GO` remains unchanged",
    ):
        assert blocker in packet

    assert (
        "publish or upload from the passing `twine`, `pipx`, or `uvx` smoke proof"
        in packet
    )
    assert "hide the Next.js npm moderate advisories" in packet
