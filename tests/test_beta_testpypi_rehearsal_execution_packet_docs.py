from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = "docs/reports/v0.10.0-beta-testpypi-rehearsal-execution-packet.md"
EXECUTION_PACKET = ROOT / PACKET_PATH


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_testpypi_rehearsal_execution_packet_exists_and_has_sections() -> None:
    assert EXECUTION_PACKET.exists()
    packet = read(EXECUTION_PACKET)

    for section in (
        "## Purpose",
        "## Current State",
        "## Required Approval Fields",
        "## Exact SHA Proof Requirements",
        "## Artifact Build Plan",
        "## Twine Check Plan",
        "## Credential Boundary",
        "## Rollback/Yank Execution-time Check",
        "## Upload Stop Rule",
        "## Explicit Non-actions",
        "## Remaining Blockers",
    ):
        assert section in packet


def test_testpypi_rehearsal_execution_packet_blocks_upload() -> None:
    packet = read(EXECUTION_PACKET)
    text = normalized(packet)
    text_lower = text.lower()

    for required in (
        "This packet does not upload.",
        "`registry_upload_executed=false`",
        "`twine upload` remains blocked",
        "credentials must not be printed",
        "`pipx install qa-z` is not live",
        "`uv tool install qa-z` is not live",
        "Release execution remains `NO-GO`.",
    ):
        assert required in packet

    for required in (
        "upload requires explicit final approval",
        "package publish proof does not exist yet",
        "no testpypi package url/version proof exists yet",
        "no pypi package url/version proof exists yet",
    ):
        assert required in text_lower


def test_testpypi_rehearsal_execution_packet_records_current_proof_inputs() -> None:
    packet = read(EXECUTION_PACKET)

    for required in (
        "`origin/main`",
        "`0c4288d98f8826e891ab8cd46fd5157000cadff0`",
        "`CI`",
        "`Public Raw Hygiene`",
        "`qa_z-0.9.8a0-py3-none-any.whl`",
        "`qa_z-0.9.8a0.tar.gz`",
        "https://pypi.org/pypi/qa-z/json",
        "https://test.pypi.org/pypi/qa-z/json",
        "HTTP 404",
    ):
        assert required in packet


def test_testpypi_rehearsal_execution_packet_keeps_pyproject_metadata_unchanged() -> (
    None
):
    pyproject = read("pyproject.toml")
    name_match = re.search(r'^name = "([^"]+)"$', pyproject, flags=re.MULTILINE)
    version_match = re.search(r'^version = "([^"]+)"$', pyproject, flags=re.MULTILINE)

    assert name_match is not None
    assert version_match is not None
    assert name_match.group(1) == "qa-z"
    assert version_match.group(1) == "0.9.8a0"


def test_testpypi_rehearsal_execution_packet_forbids_false_publish_claims() -> None:
    packet = read(EXECUTION_PACKET)

    for false_claim in (
        "TestPyPI publish completed",
        "PyPI publish completed",
        "registry_upload_executed=true",
        "pipx install qa-z is live",
        "uv tool install qa-z is live",
        "package publish proof exists",
    ):
        assert false_claim not in packet


def test_testpypi_rehearsal_execution_packet_is_linked_from_related_docs() -> None:
    for doc_path in (
        "docs/reports/v0.10.0-beta-testpypi-rehearsal-approval.md",
        "docs/reports/v0.10.0-beta-package-publish-path-decision.md",
        "docs/reports/v0.10.0-beta-release-execution-checklist.md",
        "docs/package-publish-plan.md",
    ):
        doc = read(doc_path)
        text = normalized(doc)

        assert PACKET_PATH in doc
        assert "testpypi rehearsal execution packet" in text.lower()
        assert (
            "does not upload" in text.lower()
            or "release execution remains `NO-GO`" in doc
        )
