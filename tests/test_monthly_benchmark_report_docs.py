from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_monthly_benchmark_report_template_defines_required_sections() -> None:
    docs = read("docs/monthly-benchmark-report-template.md")

    for text in (
        "Report Boundary",
        "Fixture Row Template",
        "Artifact Evidence",
        "Fixture Provenance",
        "Validation Commands",
        "Claims Boundary",
        "Generated Artifact Policy",
    ):
        assert text in docs


def test_monthly_benchmark_report_template_ties_rows_to_artifacts() -> None:
    docs = read("docs/monthly-benchmark-report-template.md")

    for text in (
        "benchmarks/fixtures/<fixture>/expected.json",
        "benchmarks/fixtures/<fixture>/repo/",
        "benchmarks/results/work/<fixture>/repo/.qa-z/",
        ".qa-z/runs/baseline/fast/summary.json",
        ".qa-z/runs/baseline/deep/summary.json",
        ".qa-z/runs/baseline/deep/results.sarif",
        ".qa-z/runs/baseline/repair/codex.md",
        ".qa-z/runs/candidate/fast/summary.json",
        ".qa-z/runs/candidate/deep/summary.json",
        ".qa-z/runs/candidate/verify/summary.json",
        ".qa-z/runs/candidate/verify/compare.json",
        ".qa-z/runs/candidate/verify/report.md",
    ):
        assert text in docs


def test_monthly_benchmark_report_template_pins_validation_and_provenance() -> None:
    docs = read("docs/monthly-benchmark-report-template.md")

    for text in (
        "python -m qa_z benchmark --fixture <fixture> --json",
        "python -m qa_z benchmark --results-dir benchmarks/results-ci --json",
        "exit code",
        "generated results directory",
        "local-only",
        "intentionally frozen",
        "expected.json is the fixture contract",
    ):
        assert text in docs


def test_monthly_benchmark_report_template_blocks_fabricated_claims() -> None:
    docs = read("docs/monthly-benchmark-report-template.md")

    for text in (
        "Do not claim",
        "adoption numbers",
        "active users",
        "customer usage",
        "production deployment",
        "performance improvement",
        "security impact",
        "leaderboard ranking",
        "model quality superiority",
        "package publishing",
        "hosted automation",
        "unless the claim is backed by sourced evidence",
    ):
        assert text in docs


def test_agent_merge_safety_benchmark_links_monthly_report_rows() -> None:
    docs = read("docs/agent-merge-safety-benchmark.md")

    for text in (
        "Monthly Report Rows",
        "docs/monthly-benchmark-report-template.md",
        "fixture name",
        "expected.json",
        "baseline/candidate QA-Z run artifacts",
        "verify verdict artifacts",
        "generated-results policy",
    ):
        assert text in docs
