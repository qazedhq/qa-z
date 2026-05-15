from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_fastapi_auth_walkthrough_names_artifact_tour_paths() -> None:
    walkthrough = read("docs/walkthroughs/auth-bug.md")

    for artifact_path in (
        ".qa-z/runs/baseline/fast/summary.json",
        ".qa-z/runs/baseline/deep/summary.json",
        ".qa-z/runs/baseline/deep/checks/sg_scan.json",
        ".qa-z/runs/baseline/deep/results.sarif",
        ".qa-z/runs/baseline/repair/codex.md",
        ".qa-z/runs/candidate/fast/summary.json",
        ".qa-z/runs/candidate/deep/summary.json",
        ".qa-z/runs/candidate/verify/summary.json",
        ".qa-z/runs/candidate/verify/compare.json",
        ".qa-z/runs/candidate/verify/report.md",
    ):
        assert artifact_path in walkthrough

    for expected_text in (
        "baseline fast evidence fails",
        "baseline deep evidence records 2 auth findings",
        "repair prompt points at the owner-check problem",
        "candidate fast and deep evidence pass",
        "verification verdict is `improved`",
        "`repair_improved` is `true`",
        "Do not commit generated `.qa-z` runtime evidence",
    ):
        assert expected_text in walkthrough


def test_fastapi_auth_readme_keeps_compact_evidence_checklist() -> None:
    readme = read("examples/fastapi-agent-bug/README.md")

    for expected_text in (
        "## Evidence checklist",
        ".qa-z/runs/baseline/fast/summary.json",
        ".qa-z/runs/baseline/deep/summary.json",
        ".qa-z/runs/baseline/repair/codex.md",
        ".qa-z/runs/candidate/verify/summary.json",
        ".qa-z/runs/candidate/verify/report.md",
        "baseline fails",
        "candidate passes",
        "verification reports `improved`",
        "Do not commit generated `.qa-z` runtime evidence",
    ):
        assert expected_text in readme
