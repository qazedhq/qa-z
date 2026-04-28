"""Architecture tests for loop-health seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.backlog_reseeding_signals as backlog_reseeding_signals_module
import qa_z.loop_health_signals as loop_health_signals_module
import qa_z.loop_history_candidates as loop_history_candidates_module


def _loop_health_function_names() -> set[str]:
    source = Path(loop_health_signals_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(loop_health_signals_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_loop_history_candidate_module_exports_match_loop_health_surface() -> None:
    assert (
        loop_history_candidates_module.discover_empty_loop_candidate_inputs
        is loop_health_signals_module.discover_empty_loop_candidate_inputs
    )
    assert (
        loop_history_candidates_module.discover_repeated_fallback_family_candidate_inputs
        is loop_health_signals_module.discover_repeated_fallback_family_candidate_inputs
    )


def test_backlog_reseeding_module_exports_match_loop_health_surface() -> None:
    assert (
        backlog_reseeding_signals_module.discover_backlog_reseeding_candidate_inputs
        is loop_health_signals_module.discover_backlog_reseeding_candidate_inputs
    )


def test_loop_health_module_keeps_candidate_defs_out_of_surface_module() -> None:
    function_names = _loop_health_function_names()

    assert "discover_empty_loop_candidate_inputs" not in function_names
    assert "discover_repeated_fallback_family_candidate_inputs" not in function_names
    assert "discover_backlog_reseeding_candidate_inputs" not in function_names
