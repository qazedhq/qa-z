"""Architecture tests for worktree discovery seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.worktree_discovery as worktree_discovery_module
import qa_z.worktree_discovery_candidates as worktree_discovery_candidates_module
import qa_z.worktree_discovery_evidence as worktree_discovery_evidence_module


def _worktree_discovery_function_names() -> set[str]:
    source = Path(worktree_discovery_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(worktree_discovery_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_worktree_candidate_module_exports_match_surface() -> None:
    assert (
        worktree_discovery_candidates_module.discover_commit_isolation_candidates
        is worktree_discovery_module.discover_commit_isolation_candidates
    )
    assert (
        worktree_discovery_candidates_module.discover_integration_gap_candidates
        is worktree_discovery_module.discover_integration_gap_candidates
    )


def test_worktree_discovery_module_keeps_candidate_defs_out_of_monolith() -> None:
    function_names = _worktree_discovery_function_names()

    assert "discover_worktree_risk_candidates" not in function_names
    assert "discover_deferred_cleanup_candidates" not in function_names
    assert "discover_commit_isolation_candidates" not in function_names
    assert "discover_artifact_hygiene_candidates" not in function_names
    assert "discover_runtime_artifact_cleanup_candidates" not in function_names
    assert "discover_evidence_freshness_candidates" not in function_names
    assert "discover_integration_gap_candidates" not in function_names


def test_worktree_evidence_module_exports_match_surface() -> None:
    assert (
        worktree_discovery_evidence_module.integration_gap_evidence
        is worktree_discovery_module.integration_gap_evidence
    )
    assert (
        worktree_discovery_evidence_module.deferred_cleanup_evidence
        is worktree_discovery_module.deferred_cleanup_evidence
    )
    assert (
        worktree_discovery_evidence_module.commit_isolation_evidence
        is worktree_discovery_module.commit_isolation_evidence
    )


def test_worktree_discovery_module_keeps_evidence_defs_out_of_monolith() -> None:
    function_names = _worktree_discovery_function_names()

    assert "integration_gap_evidence" not in function_names
    assert "deferred_cleanup_evidence" not in function_names
    assert "commit_isolation_evidence" not in function_names
    assert "artifact_hygiene_evidence" not in function_names
    assert "evidence_freshness_evidence" not in function_names
