from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROOF_REPORT = ROOT / "docs/reports/v0.10.0-beta-exact-sha-proof.md"
CANDIDATE_SHA = "865efa12fccc1976d6d9bf2cddec89bca6610f67"
PROOF_REPORT_PATH = "docs/reports/v0.10.0-beta-exact-sha-proof.md"


def read(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return " ".join(text.split())


def test_exact_sha_proof_report_exists_and_pins_candidate_sha() -> None:
    assert PROOF_REPORT.exists()
    report = read(PROOF_REPORT)

    for section in (
        "## Current Verdict",
        "## Exact Candidate SHA",
        "## Remote CI Proof",
        "## Public Raw Proof",
        "## What This Proof Establishes",
        "## What This Proof Does Not Establish",
        "## Remaining Release Blockers",
        "## Explicit Non-actions",
        "## Recommended Next Step",
    ):
        assert section in report

    match = re.search(r"Exact candidate SHA: `([0-9a-f]{40})`", report)
    assert match is not None
    assert match.group(1) == CANDIDATE_SHA
    assert (
        "Merge pull request #65 from qazedhq/codex/nextjs-advisory-decision-packet"
        in report
    )
    assert "PR #65" in report
    assert "Open GitHub issues: `0`" in report
    assert "Open GitHub pull requests: `0`" in report
    assert "`v0.10.0-beta` is not released by this packet." in report
    assert "release execution remains `NO-GO`" in report


def test_exact_sha_proof_records_remote_ci_without_pr_ci_confusion() -> None:
    report = read(PROOF_REPORT)

    for proof in (
        "| CI | `25959011641` | `push` | `main` | `completed` | `success` |",
        "| Public Raw Hygiene | `25959011658` | `push` | `main` | `completed` | `success` |",
        "https://github.com/qazedhq/qa-z/actions/runs/25959011641",
        "https://github.com/qazedhq/qa-z/actions/runs/25959011658",
    ):
        assert proof in report

    assert "Codex Review Prep" in report
    assert "PR-triggered only; no main-push run exists for this SHA." in report
    assert "| Codex Review Prep |" not in report


def test_exact_sha_proof_records_public_raw_file_access() -> None:
    report = read(PROOF_REPORT)

    for file_path in (
        "README.md",
        "pyproject.toml",
        "docs/reports/v0.10.0-beta-readiness.md",
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
        "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md",
        "docs/package-publish-plan.md",
        "scripts/package_smoke_rehearsal.py",
    ):
        assert (
            f"https://raw.githubusercontent.com/qazedhq/qa-z/{CANDIDATE_SHA}/{file_path}"
            in report
        )
        assert f"| `{file_path}` | `PASS` | `200` |" in report

    assert "`FAIL`" not in report.split("## What This Proof Establishes", 1)[0]


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

    for blocker in (
        "release-owner approval",
        "tool-equipped `twine`/`pipx`/`uvx` smoke",
        "Next.js/PostCSS advisory option and proof",
        "registry credentials",
        "package registry rollback/yank policy",
        "package metadata/version policy",
    ):
        assert blocker in report

    assert "Exact SHA proof does not replace release-owner approval." in report
    assert (
        "Exact SHA proof does not replace tool-equipped `twine`/`pipx`/`uvx` smoke."
        in report
    )
    assert "Exact SHA proof does not resolve the Next.js/PostCSS advisory." in report


def test_existing_beta_reports_link_exact_sha_proof_without_unlocking_release() -> None:
    for report_path in (
        "docs/reports/v0.10.0-beta-readiness.md",
        "docs/reports/v0.10.0-beta-release-decision.md",
        "docs/reports/v0.10.0-beta-version-policy.md",
        "docs/reports/v0.10.0-beta-nextjs-advisory-decision.md",
    ):
        report = read(ROOT / report_path)
        text = normalized(report)
        assert PROOF_REPORT_PATH in report
        assert "not release execution" in text
        assert "release execution `NO-GO`" in text
