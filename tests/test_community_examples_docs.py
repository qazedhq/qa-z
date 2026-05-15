from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_community_distribution_docs_define_required_example_evidence() -> None:
    docs = read("docs/community-distribution.md")

    for text in (
        "Community Example Submissions",
        "Required Evidence",
        "baseline command",
        "candidate command",
        "expected verdict",
        "artifact paths",
        "validation commands",
        "non-goals",
        "privacy note",
    ):
        assert text in docs


def test_community_distribution_docs_pin_artifact_policy() -> None:
    docs = read("docs/community-distribution.md")

    for allowed in (
        "source files for the minimal demo",
        "qa-z.yaml",
        "documentation explaining expected QA-Z artifact paths",
        "benchmarks/fixtures/**/repo/.qa-z/**",
    ):
        assert allowed in docs

    for forbidden in (
        "root `.qa-z/**`",
        "benchmarks/results/work/**",
        "benchmarks/results/summary.json",
        "benchmarks/results/report.md",
        "build/**",
        "dist/**",
        "src/qa_z.egg-info/**",
        ".pytest_cache/**",
        ".mypy_cache/**",
        ".ruff_cache/**",
        "secrets, credentials, tokens, API keys",
    ):
        assert forbidden in docs


def test_community_distribution_docs_include_validation_commands() -> None:
    docs = read("docs/community-distribution.md")

    for command in (
        "python -m pytest tests/test_launch_growth_package.py -q",
        "python scripts/check_text_file_hygiene.py --source working-tree --critical-profile public",
        "git diff --check",
        "qa-z fast --path examples/<example>",
        "qa-z deep --path examples/<example>",
        "qa-z repair-prompt --from-run",
        "qa-z verify --baseline-run",
    ):
        assert command in docs


def test_public_roadmap_links_community_example_guidance() -> None:
    roadmap = read("docs/public-roadmap.md")

    assert "docs/community-distribution.md" in roadmap
    assert "Community example proposals" in roadmap
    assert "required evidence" in roadmap
    assert "generated-artifact policy" in roadmap
