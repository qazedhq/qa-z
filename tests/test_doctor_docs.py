"""Docs coverage for v0.11 doctor diagnostics."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_doctor_docs_explain_environment_diagnostics_boundary() -> None:
    doctor = read("docs/doctor.md")
    readme = read("README.md")
    docs_index = read("docs/README.md")
    report = read("docs/reports/v0.11-doctor-diagnostics.md")

    for text in (
        "Run `qa-z doctor` before the first guard run",
        "installed package",
        "source checkout",
        "GitHub Actions",
        "`qa-z doctor --json`",
        "Semgrep",
        "`.qa-z` runtime directory",
        "SARIF and pull request comments are action-level opt-ins",
        "Production PyPI is not published",
        "does not upload to PyPI or TestPyPI",
    ):
        assert text in doctor

    assert "[Doctor diagnostics](docs/doctor.md)" in readme
    assert "[Doctor diagnostics](doctor.md)" in docs_index
    assert "v0.11 Doctor & Environment Diagnostics" in report
    assert "no live PyPI install claim" in report


def test_v021_doctor_docs_pin_clean_next_actions() -> None:
    doctor = read("docs/doctor.md")
    report = read("docs/reports/v0.21-first-run-onboarding.md")

    for text in (
        "Clean doctor next actions",
        "Run `qa-z demo auth-bug`.",
        "Run `qa-z scorecard`.",
        "Run `qa-z guard --adapter codex --deep auto --fail-on-risk`.",
    ):
        assert text in doctor
        assert text in report

    assert "v0.21 - First-Run Onboarding" in report
    assert "No PyPI/TestPyPI upload" in report
