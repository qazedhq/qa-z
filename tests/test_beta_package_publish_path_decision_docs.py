from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION_PATH = "docs/reports/v0.10.0-beta-package-publish-path-decision.md"
DECISION_PACKET = ROOT / DECISION_PATH


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_package_publish_path_decision_packet_exists_and_freezes_state() -> None:
    assert DECISION_PACKET.exists()
    packet = read(DECISION_PACKET)
    text = normalized(packet)

    for section in (
        "## Purpose",
        "## Current State",
        "## Decision Options",
        "## Option Comparison",
        "## Required Approval Fields",
        "## Required Proof By Option",
        "## Install Path Impact",
        "## Blocked Commands",
        "## Recommended Current Decision",
        "## Explicit Non-actions",
    ):
        assert section in packet

    assert "`v0.10.0-beta` is not released." in packet
    assert "Current public alpha remains `v0.9.9-alpha`." in packet
    assert "Current package metadata is `0.10.0b0`." in packet
    assert (
        "`registry_upload_executed=true` applies only to the historical TestPyPI"
        in packet
    )
    assert "Release execution remains `NO-GO`." in packet
    assert "Current decision: `No release yet`." in packet
    assert "no-upload tool smoke passed" in text
    assert "does not prove package publish" in text


def test_package_publish_path_decision_lists_all_release_owner_options() -> None:
    packet = read(DECISION_PACKET)

    for option in (
        "No release yet",
        "TestPyPI rehearsal only",
        "TestPyPI publish",
        "PyPI beta publish",
        "metadata-only version PR",
        "GitHub prerelease only",
    ):
        assert option in packet


def test_package_publish_path_decision_keeps_install_commands_future_only() -> None:
    packet = read(DECISION_PACKET)
    install_section = packet.split("## Install Path Impact", 1)[1]
    text = normalized(install_section)

    assert "pipx install qa-z" in install_section
    assert "uv tool install qa-z" in install_section
    assert "future pypi-published target commands" in text.lower()
    assert "not current live install claims" in text
    assert "Current active install remains GitHub source/tag install" in packet

    for false_claim in (
        "pipx install qa-z is live",
        "uv tool install qa-z is live",
        "PyPI install is available",
        "PyPI publish completed",
        "TestPyPI publish completed",
        "production registry_upload_executed=true",
    ):
        assert false_claim not in packet


def test_package_publish_path_decision_blocks_execution_actions() -> None:
    packet = read(DECISION_PACKET)

    for blocked in (
        "python -m twine upload --repository testpypi dist/*",
        "python -m twine upload dist/*",
        "git tag ...",
        "gh release create ...",
        "deploy commands",
        "changing package metadata beyond the\nowner-approved `0.10.0b0` scope",
    ):
        assert blocked in packet

    for non_action in (
        "publish to TestPyPI or PyPI",
        "run `twine upload`",
        "create a tag",
        "create a GitHub Release",
        "deploy",
        "change package metadata beyond the approved `0.10.0b0` scope",
        "load registry credentials",
        "claim `pipx install qa-z` is live",
    ):
        assert non_action in packet


def test_package_publish_path_decision_uses_owner_approved_metadata() -> None:
    pyproject = read(ROOT / "pyproject.toml")
    match = re.search(r'^version = "([^"]+)"$', pyproject, flags=re.MULTILINE)

    assert match is not None
    assert match.group(1) == "0.10.0b0"


def test_related_release_docs_link_package_publish_path_decision() -> None:
    for doc_path in (
        "docs/package-publish-plan.md",
        "docs/reports/v0.10.0-beta-no-release-decision.md",
        "docs/reports/v0.10.0-beta-release-execution-checklist.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
    ):
        doc = read(doc_path)
        text = normalized(doc)

        assert DECISION_PATH in doc
        assert "package publish path decision" in text.lower()
        assert (
            "release execution remains `NO-GO`" in text
            or "release execution `NO-GO` remains unchanged" in text
        )
