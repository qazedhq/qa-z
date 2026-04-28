"""Architecture tests for task-selection evidence rendering seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.task_selection as task_selection_module
import qa_z.task_selection_evidence as task_selection_evidence_module
import qa_z.task_selection_render as task_selection_render_module


def _task_selection_render_function_names() -> set[str]:
    source = Path(task_selection_render_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(task_selection_render_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_task_selection_evidence_module_exports_match_surface() -> None:
    assert (
        task_selection_evidence_module.compact_backlog_evidence_summary
        is task_selection_module.compact_backlog_evidence_summary
    )
    assert (
        task_selection_evidence_module.worktree_action_areas
        is task_selection_module.worktree_action_areas
    )


def test_task_selection_render_module_keeps_evidence_defs_out_of_render_module() -> (
    None
):
    function_names = _task_selection_render_function_names()

    assert "compact_backlog_evidence_summary" not in function_names
    assert "compact_action_basis" not in function_names
    assert "compact_area_action_basis" not in function_names
    assert "compact_generated_action_basis" not in function_names
    assert "worktree_action_areas" not in function_names
    assert "compact_evidence_entry" not in function_names
    assert "compact_evidence_priority" not in function_names
