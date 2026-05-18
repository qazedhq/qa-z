from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION_PACKET = ROOT / "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md"


def read(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_nextjs_advisory_decision_packet_exists_and_keeps_blocker_open() -> None:
    assert DECISION_PACKET.exists()
    packet = read(DECISION_PACKET)

    assert "Advisory remains a release blocker." in packet
    assert "GHSA-qx2v-qp2m-jg93" in packet
    assert "CVE-2026-41305" in packet
    assert "postcss <8.5.10" in packet
    assert "PostCSS 8.5.10" in packet
    assert "postcss@8.4.31" in packet
    assert "Blind Next.js major bump is not accepted as closure proof" in packet
    assert "release execution remains `NO-GO`" in packet


def test_nextjs_advisory_decision_packet_records_explicit_non_actions() -> None:
    packet = read(DECISION_PACKET)

    for non_action in (
        "No dependency update was performed.",
        "No npm audit fix was run.",
        "No package-lock.json was added.",
        "No package publish was performed.",
        "No tag was created.",
        "No GitHub Release was created.",
        "No deploy was performed.",
        "`pyproject.toml` was not changed.",
    ):
        assert non_action in packet

    for false_claim in (
        "The advisory is fixed.",
        "release execution is GO",
        "npm audit fix completed",
        "package-lock.json was committed",
        "v0.10.0-beta is released",
    ):
        assert false_claim not in packet


def test_nextjs_advisory_decision_packet_lists_release_owner_options() -> None:
    packet = read(DECISION_PACKET)

    for option in (
        "Wait for upstream Next.js/PostCSS fix",
        "Record a compatibility exception",
        "Replace the dependency",
        "Remove the Next.js demo dependency",
        "Pin or change Next.js after reviewed audit proof",
        "Explicitly defer the blocker",
        "Keep release `NO-GO`",
    ):
        assert option in packet

    for column in (
        "What it means",
        "Required proof",
        "Risks",
        "Validation commands",
        "Release impact",
        "No dependency changes?",
    ):
        assert column in packet


def test_existing_release_reports_link_nextjs_advisory_decision_packet() -> None:
    packet_path = "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md"

    for report_path in (
        "docs/reports/v0.10.0-beta-readiness.md",
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
    ):
        report = read(ROOT / report_path)
        normalized = " ".join(report.split())
        assert packet_path in report
        assert "release execution `NO-GO`" in normalized


def test_nextjs_advisory_decision_packet_preserves_separate_blockers() -> None:
    packet = read(DECISION_PACKET)

    for blocker in (
        "release-owner selected option",
        "upstream or dependency proof",
        "registry credentials",
        "rollback/yank policy",
        "version policy",
    ):
        assert blocker in packet

    assert "docs/reports/v0.10.0-beta-tool-smoke-execution.md" in packet
    assert "local no-upload" in packet
    assert "docs/reports/v0.10.0-beta-exact-sha-proof.md" in packet
    assert "docs/reports/v0.10.0-beta-final-sha-proof-protocol.md" in packet
    assert "final release-execution-time SHA proof" in packet
