"""Tests for self-improvement discovery wrapper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.self_improvement as self_improvement_module
import qa_z.self_improvement_discovery as self_improvement_discovery_module


def test_self_improvement_discovery_module_exports_match_self_improvement_surface() -> (
    None
):
    assert (
        self_improvement_discovery_module.discover_benchmark_candidates
        is self_improvement_module.discover_benchmark_candidates
    )
    assert (
        self_improvement_discovery_module.discover_backlog_reseeding_candidates
        is self_improvement_module.discover_backlog_reseeding_candidates
    )


def test_self_improvement_discovery_benchmark_candidate_formats_snapshot(
    tmp_path: Path,
) -> None:
    candidate = self_improvement_discovery_module.benchmark_candidate(
        tmp_path,
        tmp_path / "benchmarks" / "results" / "summary.json",
        "mixed-surface-fast",
        failures=["fixture mismatch", "report missing"],
        snapshot="1/2 fixtures, overall_rate 0.5",
    )

    assert candidate.id == "benchmark_gap-mixed-surface-fast"
    assert candidate.evidence == [
        {
            "source": "benchmark",
            "path": "benchmarks/results/summary.json",
            "summary": (
                "snapshot=1/2 fixtures, overall_rate 0.5; "
                "fixture=mixed-surface-fast; failures=fixture mismatch; report missing"
            ),
        }
    ]


def test_self_improvement_module_keeps_discovery_wrapper_defs_out_of_monolith() -> None:
    source = Path(self_improvement_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(self_improvement_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "discover_benchmark_candidates" not in function_names
    assert "benchmark_candidate" not in function_names
    assert "discover_empty_loop_candidates" not in function_names
    assert "discover_repeated_fallback_family_candidates" not in function_names
    assert "discover_backlog_reseeding_candidates" not in function_names
