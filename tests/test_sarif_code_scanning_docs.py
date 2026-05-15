from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_sarif_code_scanning_walkthrough_pins_upload_and_inspection_flow() -> None:
    docs = read("docs/walkthroughs/sarif-code-scanning.md")

    for text in (
        ".qa-z/runs/<run-id>/deep/results.sarif",
        ".qa-z/runs/ci/deep/results.sarif",
        "github/codeql-action/upload-sarif@v4",
        "security-events: write",
        "qa-z-semgrep",
        "GitHub code scanning",
        "SARIF upload is optional",
        "docs/assets/sarif-code-scanning-capture.md",
        "does not post pull request comments",
        "commit",
        "push",
        "tag",
        "release",
        "deploy",
        "live model APIs",
    ):
        assert text in docs


def test_sarif_code_scanning_capture_is_sanitized() -> None:
    capture = read("docs/assets/sarif-code-scanning-capture.md")

    for text in (
        "sanitized textual capture",
        "qa-z-semgrep",
        ".qa-z/runs/ci/deep/results.sarif",
        "Private data intentionally omitted",
        "private repository names",
        "repository-private file contents",
        "tokens",
        "secrets",
        "user emails",
    ):
        assert text in capture
