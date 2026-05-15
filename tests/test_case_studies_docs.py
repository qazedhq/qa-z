from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_case_studies_docs_define_required_template_sections() -> None:
    docs = read("docs/case-studies.md")

    for text in (
        "Case Study Template",
        "When To Use This Template",
        "Required Sections",
        "Before/After Evidence Checklist",
        "Command Template",
        "Artifact Pointers",
        "Validation",
        "Redaction And Privacy",
        "Non-Goals",
        "Claims Boundary",
        "Generated Artifact Policy",
    ):
        assert text in docs


def test_case_studies_docs_pin_before_after_evidence_artifacts() -> None:
    docs = read("docs/case-studies.md")

    for path in (
        ".qa-z/runs/<baseline>/fast/summary.json",
        ".qa-z/runs/<baseline>/deep/summary.json",
        ".qa-z/runs/<baseline>/deep/results.sarif",
        ".qa-z/runs/<baseline>/repair/codex.md",
        ".qa-z/runs/<candidate>/fast/summary.json",
        ".qa-z/runs/<candidate>/deep/summary.json",
        ".qa-z/runs/<candidate>/verify/summary.json",
        ".qa-z/runs/<candidate>/verify/compare.json",
        ".qa-z/runs/<candidate>/verify/report.md",
    ):
        assert path in docs


def test_case_studies_docs_include_command_template() -> None:
    docs = read("docs/case-studies.md")

    for command in (
        "qa-z fast --output-dir .qa-z/runs/baseline",
        "qa-z deep --from-run .qa-z/runs/baseline",
        "qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex",
        "qa-z fast --output-dir .qa-z/runs/candidate",
        "qa-z deep --from-run .qa-z/runs/candidate",
        "qa-z verify --baseline-run .qa-z/runs/baseline --candidate-run .qa-z/runs/candidate",
    ):
        assert command in docs


def test_case_studies_docs_prevent_fake_adoption_and_customer_claims() -> None:
    docs = read("docs/case-studies.md")

    for text in (
        "Do not claim",
        "customer uses QA-Z unless the customer explicitly approved",
        "adoption counts",
        "user counts",
        "star counts",
        "deployment counts",
        "revenue impact",
        "unless they are sourced",
        "security impact beyond what the QA-Z artifacts prove",
    ):
        assert text in docs


def test_case_studies_docs_require_redaction_and_generated_artifact_policy() -> None:
    docs = read("docs/case-studies.md")

    for text in (
        "secrets, tokens, API keys, credentials",
        "private repository names",
        "private file paths",
        "customer names",
        "user emails and personal data",
        "proprietary source snippets",
        "internal branch names, ticket IDs, or URLs",
        "root `.qa-z/**`",
        "benchmarks/results/work/**",
        "benchmarks/results/summary.json",
        "benchmarks/results/report.md",
        "build/**",
        "dist/**",
        ".pytest_cache/**",
        ".mypy_cache/**",
        ".ruff_cache/**",
        "benchmarks/fixtures/**/repo/.qa-z/**",
    ):
        assert text in docs
