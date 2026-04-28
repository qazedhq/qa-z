"""Coverage-gap discovery helpers for mixed-surface benchmark realism."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.backlog_core import BacklogCandidate, format_report_evidence
from qa_z.benchmark_contracts import BenchmarkExpectation
from qa_z.report_matching import matching_report_evidence
from qa_z.self_improvement_constants import REPORT_EVIDENCE_FILES
from qa_z.self_improvement_runtime import read_json_object

__all__ = [
    "discover_coverage_gap_candidates",
    "mixed_surface_coverage_evidence",
]


def discover_coverage_gap_candidates(root: Path) -> list[Any]:
    """Create candidates from benchmark realism and coverage gaps."""
    evidence = mixed_surface_coverage_evidence(root)
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="coverage_gap-mixed-surface-benchmark-realism",
            title="Expand executed mixed-surface benchmark realism",
            category="coverage_gap",
            evidence=evidence,
            impact=4,
            likelihood=4,
            confidence=3,
            repair_cost=3,
            recommendation="add_benchmark_fixture",
            signals=[
                "mixed_surface_realism_gap",
                "roadmap_gap",
                "service_readiness_gap",
            ],
        )
    ]


def mixed_surface_coverage_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect evidence that mixed-surface executed benchmark coverage is thin."""
    fixtures_root = root / "benchmarks" / "fixtures"
    evidence: list[dict[str, Any]] = []
    if fixtures_root.is_dir():
        covered_modes = mixed_surface_run_modes(fixtures_root)
        has_fixture_contracts = has_any_fixture_contract(fixtures_root)
        missing_modes = [
            mode for mode in ("fast", "deep", "handoff") if mode not in covered_modes
        ]
        if covered_modes and missing_modes:
            evidence.append(
                {
                    "source": "benchmark_fixtures",
                    "path": format_path(fixtures_root, root),
                    "summary": (
                        "executed mixed coverage still missing: "
                        + ", ".join(missing_modes)
                    ),
                }
            )
        elif fixtures_root.exists() and has_any_mixed_fixture(fixtures_root):
            missing_modes = ["fast", "deep", "handoff"]
        elif has_fixture_contracts:
            missing_modes = ["fast", "deep", "handoff"]
        else:
            missing_modes = []
        if missing_modes and not covered_modes:
            evidence.append(
                {
                    "source": "benchmark_fixtures",
                    "path": format_path(fixtures_root, root),
                    "summary": (
                        "executed mixed coverage is still missing: "
                        + ", ".join(missing_modes)
                    ),
                }
            )
    evidence.extend(
        format_report_evidence(
            root,
            matching_report_evidence(
                root,
                report_evidence_files=REPORT_EVIDENCE_FILES,
                sources={"current_state", "roadmap"},
                terms=(
                    "mixed-surface executed benchmark expansion",
                    "mixed-surface behavior",
                    "mixed-language verification coverage exists, but executed mixed-surface",
                    "current mixed coverage leans on seeded verification artifacts",
                ),
                summary="report calls out remaining executed mixed-surface benchmark realism work",
            ),
        )
    )
    return evidence


def mixed_surface_run_modes(fixtures_root: Path) -> set[str]:
    """Return executed modes represented by mixed-surface benchmark fixtures."""
    covered_modes: set[str] = set()
    for path in fixtures_root.glob("*/expected.json"):
        payload = read_json_object(path)
        if not payload:
            continue
        name = str(payload.get("name") or path.parent.name).strip()
        if "mixed" not in name.lower():
            continue
        try:
            expectation = BenchmarkExpectation.from_dict(payload)
        except ValueError:
            continue
        if expectation.should_run_fast():
            covered_modes.add("fast")
        if expectation.should_run_deep():
            covered_modes.add("deep")
        if expectation.should_run_handoff():
            covered_modes.add("handoff")
    return covered_modes


def has_any_mixed_fixture(fixtures_root: Path) -> bool:
    """Return whether any mixed-surface fixture exists in the corpus."""
    for path in fixtures_root.glob("*/expected.json"):
        payload = read_json_object(path)
        name = str(payload.get("name") or path.parent.name).strip()
        if "mixed" in name.lower():
            return True
    return False


def has_any_fixture_contract(fixtures_root: Path) -> bool:
    """Return whether any benchmark fixture expected.json exists in the corpus."""
    return any(fixtures_root.glob("*/expected.json"))
