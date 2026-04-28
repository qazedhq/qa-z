"""Tests for coverage-gap discovery helpers."""

from __future__ import annotations

from pathlib import Path

from qa_z.coverage_gap_discovery import (
    discover_coverage_gap_candidates,
    mixed_surface_coverage_evidence,
)
from tests.self_improvement_test_support import (
    write_fixture_expectation,
    write_fixture_index,
    write_report,
)


def test_mixed_surface_coverage_evidence_skips_when_executed_fixture_exists(
    tmp_path: Path,
) -> None:
    write_fixture_index(tmp_path, ["py_type_error"])
    write_fixture_expectation(
        tmp_path,
        "mixed-fast-realism",
        {"name": "mixed-fast-realism", "run": {"fast": True}},
    )
    write_fixture_expectation(
        tmp_path,
        "mixed-deep-realism",
        {"name": "mixed-deep-realism", "run": {"deep": True}},
    )
    write_fixture_expectation(
        tmp_path,
        "mixed-handoff-realism",
        {"name": "mixed-handoff-realism", "run": {"repair_handoff": True}},
    )

    assert mixed_surface_coverage_evidence(tmp_path) == []
    assert discover_coverage_gap_candidates(tmp_path) == []


def test_discover_coverage_gap_candidates_combines_fixture_and_report_evidence(
    tmp_path: Path,
) -> None:
    write_fixture_index(tmp_path, ["py_type_error"])
    write_fixture_expectation(
        tmp_path,
        "mixed-fast-handoff-realism",
        {
            "name": "mixed-fast-handoff-realism",
            "run": {"fast": True, "repair_handoff": True},
        },
    )
    write_report(
        tmp_path,
        "next-improvement-roadmap.md",
        """
        # QA-Z Next Improvement Roadmap

        mixed-surface executed benchmark expansion remains open while current mixed
        coverage leans on seeded verification artifacts.
        """,
    )

    candidates = discover_coverage_gap_candidates(tmp_path)

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.category == "coverage_gap"
    assert candidate.recommendation == "add_benchmark_fixture"
    assert candidate.signals == [
        "mixed_surface_realism_gap",
        "roadmap_gap",
        "service_readiness_gap",
    ]
    assert candidate.evidence == [
        {
            "source": "benchmark_fixtures",
            "path": "benchmarks/fixtures",
            "summary": ("executed mixed coverage still missing: deep"),
        },
        {
            "source": "roadmap",
            "path": "docs/reports/next-improvement-roadmap.md",
            "summary": "report calls out remaining executed mixed-surface benchmark realism work",
        },
    ]


def test_discover_coverage_gap_candidates_when_no_mixed_fixture_exists(
    tmp_path: Path,
) -> None:
    write_fixture_index(tmp_path, ["py_type_error"])

    candidates = discover_coverage_gap_candidates(tmp_path)

    assert len(candidates) == 1
    assert candidates[0].evidence == [
        {
            "source": "benchmark_fixtures",
            "path": "benchmarks/fixtures",
            "summary": "executed mixed coverage is still missing: fast, deep, handoff",
        }
    ]


def test_discover_coverage_gap_candidates_keeps_report_only_evidence(
    tmp_path: Path,
) -> None:
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Current mixed coverage leans on seeded verification artifacts.
        """,
    )

    candidates = discover_coverage_gap_candidates(tmp_path)

    assert len(candidates) == 1
    assert candidates[0].evidence == [
        {
            "source": "current_state",
            "path": "docs/reports/current-state-analysis.md",
            "summary": "report calls out remaining executed mixed-surface benchmark realism work",
        }
    ]
