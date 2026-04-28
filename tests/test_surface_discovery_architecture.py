"""Architecture tests for surface-discovery seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.artifact_consistency_discovery as artifact_consistency_discovery_module
import qa_z.coverage_gap_discovery as coverage_gap_discovery_module
import qa_z.docs_surface_discovery as docs_surface_discovery_module
import qa_z.surface_discovery as surface_discovery_module


def _surface_discovery_function_names() -> set[str]:
    source = Path(surface_discovery_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(surface_discovery_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_artifact_consistency_module_exports_match_surface() -> None:
    assert (
        artifact_consistency_discovery_module.discover_artifact_consistency_candidates
        is surface_discovery_module.discover_artifact_consistency_candidates
    )


def test_docs_surface_module_exports_match_surface() -> None:
    assert (
        docs_surface_discovery_module.discover_docs_drift_candidates
        is surface_discovery_module.discover_docs_drift_candidates
    )


def test_coverage_gap_module_exports_match_surface() -> None:
    assert (
        coverage_gap_discovery_module.discover_coverage_gap_candidates
        is surface_discovery_module.discover_coverage_gap_candidates
    )


def test_surface_discovery_module_keeps_split_defs_out_of_surface() -> None:
    function_names = _surface_discovery_function_names()

    assert "discover_artifact_consistency_candidates" not in function_names
    assert "discover_docs_drift_candidates" not in function_names
    assert "discover_coverage_gap_candidates" not in function_names
    assert "mixed_surface_coverage_evidence" not in function_names
