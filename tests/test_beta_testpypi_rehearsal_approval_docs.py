from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PATH = "docs/reports/v0.10.0-beta-testpypi-rehearsal-approval.md"
APPROVAL_PACKET = ROOT / APPROVAL_PATH


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_testpypi_rehearsal_approval_packet_exists_and_has_sections() -> None:
    assert APPROVAL_PACKET.exists()
    packet = read(APPROVAL_PACKET)

    for section in (
        "## Purpose",
        "## Current State",
        "## Selected Next Path",
        "## What This Approval Does Not Authorize",
        "## Required Before Actual TestPyPI Upload",
        "## Required Evidence",
        "## Blocked Commands",
        "## Remaining Blockers",
        "## Explicit Non-actions",
    ):
        assert section in packet


def test_testpypi_rehearsal_approval_records_selected_path_not_upload() -> None:
    packet = read(APPROVAL_PACKET)
    text = normalized(packet)

    for required in (
        "Selected next path: TestPyPI rehearsal.",
        "`v0.10.0-beta` is not released.",
        "Current package metadata remains `0.9.8a0`.",
        "`registry_upload_executed=false`",
        "no-upload tool smoke passed",
        "This approval does not authorize upload yet.",
        "`PACKAGE_PUBLISH_ALLOWED=true`",
        "exact release SHA proof",
        "registry credential boundary",
        "rollback/yank policy check",
        "final execution packet",
    ):
        assert required in packet

    assert "no-upload smoke is not TestPyPI publish proof" in text
    assert "release execution remains `NO-GO`" in text


def test_testpypi_rehearsal_approval_blocks_publish_actions() -> None:
    packet = read(APPROVAL_PACKET)

    for blocked in (
        "python -m twine upload --repository testpypi dist/*",
        "python -m twine upload dist/*",
        "git tag ...",
        "gh release create ...",
        "deploy commands",
    ):
        assert blocked in packet

    for non_action in (
        "publish to TestPyPI",
        "publish to PyPI",
        "run `twine upload`",
        "create a tag",
        "create a GitHub Release",
        "deploy",
        "change `pyproject.toml`",
        "bump version metadata",
        "load registry credentials",
        "claim `pipx install qa-z` is live",
        "commit generated artifacts",
    ):
        assert non_action in packet

    for false_claim in (
        "TestPyPI publish completed",
        "PyPI publish completed",
        "registry_upload_executed=true",
        "pipx install qa-z is live",
        "uv tool install qa-z is live",
    ):
        assert false_claim not in packet


def test_testpypi_rehearsal_approval_keeps_historical_packet_separate() -> None:
    pyproject = read("pyproject.toml")
    match = re.search(r'^version = "([^"]+)"$', pyproject, flags=re.MULTILINE)
    packet = read(APPROVAL_PACKET)

    assert match is not None
    assert match.group(1) == "0.10.0b0"
    assert "Current package metadata remains `0.9.8a0`." in packet


def test_testpypi_rehearsal_approval_is_linked_from_related_docs() -> None:
    for doc_path in (
        "docs/reports/v0.10.0-beta-package-publish-path-decision.md",
        "docs/reports/v0.10.0-beta-no-release-decision.md",
        "docs/reports/v0.10.0-beta-release-execution-checklist.md",
        "docs/package-publish-plan.md",
    ):
        doc = read(doc_path)
        text = normalized(doc)

        assert APPROVAL_PATH in doc
        assert "testpypi rehearsal approval" in text.lower()
        assert (
            "does not authorize upload" in text.lower()
            or "release execution remains `NO-GO`" in text
        )
