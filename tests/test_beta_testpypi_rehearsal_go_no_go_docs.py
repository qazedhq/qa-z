from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET_PATH = "docs/reports/v0.10.0-beta-testpypi-rehearsal-go-no-go.md"
PACKET = ROOT / PACKET_PATH


def read(path: str | Path) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_testpypi_rehearsal_go_no_go_packet_exists_and_has_sections() -> None:
    assert PACKET.exists()
    packet = read(PACKET)

    for section in (
        "## Purpose",
        "## Frozen Candidate SHA",
        "## Remote Proof",
        "## Package Metadata",
        "## External Release State",
        "## Artifact Build Proof",
        "## Twine Check Proof",
        "## Artifact Smoke Proof",
        "## Credential Boundary",
        "## Rollback/Yank Policy Check",
        "## Advisory Proof Check",
        "## Generated Artifact Cleanup Proof",
        "## Decision Matrix",
        "## Upload Stop Rule",
        "## Explicit Non-actions",
        "## Remaining Blockers",
    ):
        assert section in packet


def test_testpypi_rehearsal_go_no_go_records_no_go_decision() -> None:
    packet = read(PACKET)
    text = normalized(packet)

    for required in (
        "Decision: `NO_GO_MISSING_APPROVAL`.",
        "Primary decision: `NO_GO_MISSING_APPROVAL`.",
        "`GO_FOR_TESTPYPI_UPLOAD` | `NO`",
        "`NO_GO_MISSING_APPROVAL` | `ACTIVE`",
        "`NO_GO_MISSING_CREDENTIALS` | `ACTIVE`",
        "`NO_GO_POLICY_BLOCKER` | `ACTIVE`",
        "`registry_upload_executed=false`",
        "`twine upload` remains blocked",
        "This packet does not upload.",
    ):
        assert required in packet

    assert (
        "`RELEASE_EXECUTION_APPROVED=true` and `PACKAGE_PUBLISH_ALLOWED=true`" in text
    )
    assert "package publish proof does not exist yet" in text.lower()


def test_testpypi_rehearsal_go_no_go_records_sha_checks_and_metadata() -> None:
    packet = read(PACKET)
    pyproject = read("pyproject.toml")
    name_match = re.search(r'^name = "([^"]+)"$', pyproject, flags=re.MULTILINE)
    version_match = re.search(r'^version = "([^"]+)"$', pyproject, flags=re.MULTILINE)

    assert "`b8f6df2a1f822055eebc9d6368db03682057936e`" in packet
    assert "candidate SHA and `origin/main` matched" in packet
    assert "GitHub Actions run `26230481473`" in packet
    assert "GitHub Actions run `26230481480`" in packet

    assert name_match is not None
    assert version_match is not None
    assert name_match.group(1) == "qa-z"
    assert version_match.group(1) == "0.10.0b0"
    assert "| package name | `PASS` | `qa-z` |" in packet
    assert "| package version | `PASS` | `0.9.8a0` |" in packet


def test_testpypi_rehearsal_go_no_go_records_artifact_and_twine_proof() -> None:
    packet = read(PACKET)

    for required in (
        "`qa_z-0.9.8a0-py3-none-any.whl`",
        "`qa_z-0.9.8a0.tar.gz`",
        "`29df2346e4fe2abaed1a380f87a327606317797851bfd839463640e391c2cd6e`",
        "`a91f99c954a27b3567090407e3e8be2229f2e5aeb8b28493c031c78084acbd70`",
        "twine version 6.2.0",
        "Result: `PASS`.",
        "Both artifacts were checked and reported `PASSED`.",
        "| `twine_check` | `PASS` |",
        "| `pipx_wheel_help` | `NOT RUN` |",
        "| `uvx_wheel_help` | `NOT RUN` |",
    ):
        assert required in packet

    assert "No `twine upload` command was run." in packet


def test_testpypi_rehearsal_go_no_go_records_credential_and_policy_blockers() -> None:
    packet = read(PACKET)
    text = normalized(packet)

    for credential in (
        "`TWINE_USERNAME` | absent",
        "`TWINE_PASSWORD` | absent",
        "`TWINE_API_TOKEN` | absent",
        "`TESTPYPI_API_TOKEN` | absent",
        "`TEST_PYPI_API_TOKEN` | absent",
        "`UV_PUBLISH_TOKEN` | absent",
        "`PYPI_API_TOKEN` | absent",
    ):
        assert credential in packet

    assert "Values were not printed." in packet
    assert "Credential presence is not approval." in packet
    assert "https://docs.pypi.org/project-management/yanking/" in packet
    assert "https://docs.pypi.org/project-management/storage-limits/" in packet
    assert "https://github.com/advisories/GHSA-qx2v-qp2m-jg93" in packet
    assert "https://nvd.nist.gov/vuln/detail/CVE-2026-41305" in packet
    assert "affected versions `< 8.5.10`" in text
    assert "patched version `8.5.10`" in text


def test_testpypi_rehearsal_go_no_go_forbids_false_publish_claims() -> None:
    packet = read(PACKET)

    for false_claim in (
        "TestPyPI publish completed",
        "PyPI publish completed",
        "registry_upload_executed=true",
        "pipx install qa-z is live",
        "uv tool install qa-z is live",
        "package publish proof exists",
        "GO_FOR_TESTPYPI_UPLOAD` | `YES",
    ):
        assert false_claim not in packet


def test_testpypi_rehearsal_go_no_go_is_linked_from_related_docs() -> None:
    for doc_path in (
        "docs/reports/v0.10.0-beta-testpypi-rehearsal-approval.md",
        "docs/reports/v0.10.0-beta-package-publish-path-decision.md",
        "docs/reports/v0.10.0-beta-release-execution-checklist.md",
        "docs/reports/v0.10.0-beta-testpypi-rehearsal-execution-packet.md",
        "docs/package-publish-plan.md",
    ):
        doc = read(doc_path)
        text = normalized(doc)

        assert PACKET_PATH in doc
        assert "testpypi rehearsal go/no-go" in text.lower()
        assert (
            "does not upload" in text.lower()
            or "release execution remains `NO-GO`" in doc
        )
