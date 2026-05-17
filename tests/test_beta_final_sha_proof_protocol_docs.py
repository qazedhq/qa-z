from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/reports/v0.10.0-beta-final-sha-proof-protocol.md"
EXACT_PROOF = ROOT / "docs/reports/v0.10.0-beta-exact-sha-proof.md"
PROTOCOL_PATH = "docs/reports/v0.10.0-beta-final-sha-proof-protocol.md"


def read(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_final_sha_proof_protocol_exists_and_explains_pr_loop() -> None:
    assert PROTOCOL.exists()
    protocol = read(PROTOCOL)
    text = normalized(protocol)

    for section in (
        "## Purpose",
        "## Why PR-committed Proof Becomes Historical",
        "## Historical Proof vs Final Release Proof",
        "## Release-candidate SHA Freeze",
        "## Required Final Proof Fields",
        "## Allowed Storage Locations",
        "## Disallowed Actions",
        "## Release-owner Checklist",
        "## Remaining Blockers",
        "## Recommended Next Step",
    ):
        assert section in protocol

    assert (
        "A proof committed to `main` changes `main` when the proof PR is merged."
        in (protocol)
    )
    assert "PR-committed exact SHA proof becomes historical after merge" in text
    assert "Creating another PR whose only purpose is to refresh main SHA proof" in (
        protocol
    )
    assert "repeats the same loop" in text


def test_final_sha_proof_must_follow_release_candidate_freeze() -> None:
    protocol = read(PROTOCOL)
    text = normalized(protocol)

    assert "Final proof must be generated after this freeze" in protocol
    assert "release-candidate SHA is frozen" in text
    assert "final freshness check" in text
    assert "If storing the proof changes the candidate SHA" in protocol
    assert "that proof is historical, not final" in text


def test_final_sha_proof_protocol_records_required_fields_and_storage() -> None:
    protocol = read(PROTOCOL)

    for required_field in (
        "exact release-candidate SHA",
        "`CI` run ID",
        "`Public Raw Hygiene` run ID",
        "exact-SHA public raw accessibility",
        "package smoke status",
        "`twine`, `pipx`, and `uvx`",
        "Next.js/PostCSS advisory decision status",
        "package metadata/version decision",
        "registry credential state",
        "rollback/yank policy",
        "release-owner approval fields",
    ):
        assert required_field in protocol

    for location in (
        "release execution packet",
        "release-candidate branch artifact",
        "GitHub Actions artifact",
        "approved release notes attachment",
        "local operator evidence bundle",
    ):
        assert location in protocol


def test_final_sha_proof_protocol_does_not_authorize_release_actions() -> None:
    protocol = read(PROTOCOL)

    for disallowed in (
        "creating tags",
        "creating GitHub Releases",
        "publishing packages",
        "running `twine upload`",
        "deploying",
        "changing `pyproject.toml`",
        "bumping version metadata",
        "mutating GitHub settings",
        "posting bot comments",
        "calling live model APIs",
        "committing generated artifacts",
    ):
        assert disallowed in protocol

    for false_claim in (
        "v0.10.0-beta is released",
        "release execution is `GO`",
        "PyPI publish completed",
        "TestPyPI publish completed",
        "registry_upload_executed=true",
    ):
        assert false_claim not in protocol


def test_final_sha_proof_protocol_preserves_remaining_blockers() -> None:
    protocol = read(PROTOCOL)

    for blocker in (
        "release-owner approval",
        "final release-execution-time SHA proof",
        "Next.js/PostCSS advisory option and proof",
        "registry credentials",
        "package metadata/version execution decision",
        "package registry rollback/yank policy",
    ):
        assert blocker in protocol

    assert "Tool-equipped no-upload package smoke has passed" in protocol
    assert "Refresh package-smoke proof if the release" in protocol
    assert "credentials are not approval" in protocol
    assert (
        "Final proof must be generated after the release-candidate SHA is frozen"
        in (normalized(protocol))
    )


def test_exact_sha_proof_report_links_to_final_protocol() -> None:
    report = read(EXACT_PROOF)
    text = normalized(report)

    assert PROTOCOL_PATH in report
    assert "historical proof" in text
    assert "final release proof" in text
    assert "outside the PR-merge loop" in text


def test_release_reports_link_to_final_sha_proof_protocol() -> None:
    for report_path in (
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-readiness.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
        "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md",
    ):
        report = read(ROOT / report_path)
        text = normalized(report)
        assert PROTOCOL_PATH in report
        assert (
            "release execution `NO-GO`" in text
            or "release execution remains `NO-GO`" in text
        )
        assert "not release execution" in text
