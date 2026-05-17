from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROOF_REPORT = ROOT / "docs/reports/v0.10.0-beta-exact-sha-proof.md"
HISTORICAL_SHA = "865efa12fccc1976d6d9bf2cddec89bca6610f67"
POST_MERGE_SHA = "7ec919b8ed255e623c7b684d296d8256d82d16ca"
PR_67_MERGE_SHA = "31706c0c7843ecac0c6e1a401ac0e5b762e27bc5"
PROOF_REPORT_PATH = "docs/reports/v0.10.0-beta-exact-sha-proof.md"
FINAL_PROTOCOL_PATH = "docs/reports/v0.10.0-beta-final-sha-proof-protocol.md"


def read(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def section(text: str, heading: str, next_heading: str) -> str:
    return text.split(heading, 1)[1].split(next_heading, 1)[0]


def test_exact_sha_proof_report_exists_and_records_historical_pr_proof() -> None:
    assert PROOF_REPORT.exists()
    report = read(PROOF_REPORT)

    for report_section in (
        "## Current Verdict",
        "## Historical Pre-packet Proof",
        "## Historical PR #67 Proof Target",
        "## Remote CI Proof",
        "## Public Raw Proof",
        "## Historical Gate Delta",
        "## What This Proof Establishes",
        "## What This Proof Does Not Establish",
        "## Remaining Release Blockers",
        "## Explicit Non-actions",
        "## Recommended Next Step",
    ):
        assert report_section in report

    assert f"Historical pre-packet SHA:\n`{HISTORICAL_SHA}`" in report
    assert f"Historical PR #67 proof target SHA:\n`{POST_MERGE_SHA}`" in report
    assert PR_67_MERGE_SHA in report
    assert FINAL_PROTOCOL_PATH in report
    assert "PR #65" in report
    assert "PR #66" in report
    assert "PR #67" in report
    assert "`v0.10.0-beta` is not released by this packet." in report
    assert "release execution remains `NO-GO`" in report


def test_exact_sha_proof_distinguishes_historical_and_final_proof() -> None:
    report = read(PROOF_REPORT)
    text = normalized(report)

    assert "historical pre-packet proof" in text
    assert "This proof is historical proof only." in report
    assert "became historical proof for this exact SHA" in report
    assert (
        "Final release execution proof must be generated after release-candidate"
        in report
    )
    assert (
        "Merge pull request #65 from qazedhq/codex/nextjs-advisory-decision-packet"
        in (report)
    )
    assert "Merge pull request #66 from qazedhq/codex/v010-beta-exact-sha-proof" in (
        report
    )

    gate_delta = section(
        report,
        "## Historical Gate Delta",
        "## What This Proof Establishes",
    )
    assert "| PR #67 exact SHA refresh | `HISTORICAL` |" in gate_delta
    assert "| final release-execution-time SHA proof | `BLOCKED` |" in gate_delta

    remaining = section(
        report,
        "## Remaining Release Blockers",
        "## Explicit Non-actions",
    )
    assert "final release-execution-time SHA proof" in remaining


def test_exact_sha_proof_records_current_remote_ci_without_pr_ci_confusion() -> None:
    report = read(PROOF_REPORT)

    for proof in (
        "| CI | `25976157325` | `push` | `main` | `completed` | `success` |",
        "| Public Raw Hygiene | `25976157333` | `push` | `main` | `completed` | `success` |",
        "https://github.com/qazedhq/qa-z/actions/runs/25976157325",
        "https://github.com/qazedhq/qa-z/actions/runs/25976157333",
    ):
        assert proof in report

    assert "Codex Review Prep" in report
    assert "not applicable / PR-triggered only; no main-push run exists" in report
    assert "| Codex Review Prep |" not in report


def test_exact_sha_proof_records_current_public_raw_file_access() -> None:
    report = read(PROOF_REPORT)

    for file_path in (
        "README.md",
        "pyproject.toml",
        "docs/reports/v0.10.0-beta-readiness.md",
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
        "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md",
        "docs/reports/v0.10.0-beta-exact-sha-proof.md",
        "scripts/package_smoke_rehearsal.py",
    ):
        assert (
            f"https://raw.githubusercontent.com/qazedhq/qa-z/{POST_MERGE_SHA}/{file_path}"
            in report
        )
        assert f"| `{file_path}` | `PASS` | `200` |" in report

    current_raw = section(
        report,
        "## Public Raw Proof",
        "## Historical Gate Delta",
    )
    assert "`FAIL`" not in current_raw


def test_exact_sha_proof_keeps_release_actions_explicitly_absent() -> None:
    report = read(PROOF_REPORT)

    for non_action in (
        "No tag was created.",
        "No GitHub Release was created.",
        "No package publish occurred.",
        "No deploy occurred.",
        "No `pyproject.toml` version bump occurred.",
        "No `twine upload` command was run.",
        "No GitHub settings mutation or bot comment occurred.",
        "No live model API call occurred.",
    ):
        assert non_action in report

    for false_claim in (
        "v0.10.0-beta is released.",
        "registry_upload_executed=true",
        "PyPI publish completed",
        "TestPyPI publish completed",
        "release execution is `GO`",
    ):
        assert false_claim not in report


def test_exact_sha_proof_preserves_remaining_blockers() -> None:
    report = read(PROOF_REPORT)
    remaining = section(
        report,
        "## Remaining Release Blockers",
        "## Explicit Non-actions",
    )

    for blocker in (
        "release-owner approval",
        "tool-equipped `twine`/`pipx`/`uvx` smoke",
        "Next.js/PostCSS advisory option and proof",
        "registry credentials",
        "package registry rollback/yank policy",
        "package metadata/version policy",
        "final release-execution-time SHA proof",
    ):
        assert blocker in remaining

    assert "Exact SHA proof does not replace release-owner approval." in report
    assert (
        "Exact SHA proof does not replace tool-equipped `twine`/`pipx`/`uvx` smoke."
        in report
    )
    assert "Exact SHA proof does not resolve the Next.js/PostCSS advisory." in report
    assert "Exact SHA proof does not provide registry credentials." in report
    assert (
        "Exact SHA proof does not provide package registry rollback/yank policy."
        in report
    )
    assert "Exact SHA proof committed through a PR does not provide final" in report


def test_existing_beta_reports_link_current_exact_sha_proof_without_unlocking_release() -> (
    None
):
    for report_path in (
        "docs/reports/v0.10.0-beta-readiness.md",
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
        "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md",
    ):
        report = read(ROOT / report_path)
        text = normalized(report)
        assert PROOF_REPORT_PATH in report
        assert FINAL_PROTOCOL_PATH in report
        assert "not release execution" in text
        assert "release execution `NO-GO`" in text
