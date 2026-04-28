"""Architecture tests for task-selection seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.task_selection as task_selection_module
import qa_z.task_selection_core as task_selection_core_module
import qa_z.task_selection_render as task_selection_render_module


def _task_selection_function_names() -> set[str]:
    source = Path(task_selection_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(task_selection_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_task_selection_core_module_exports_match_surface() -> None:
    assert (
        task_selection_core_module.apply_selection_penalty
        is task_selection_module.apply_selection_penalty
    )
    assert (
        task_selection_core_module.select_items_with_batch_diversity
        is task_selection_module.select_items_with_batch_diversity
    )
    assert (
        task_selection_core_module.fallback_family_for_category
        is task_selection_module.fallback_family_for_category
    )


def test_task_selection_module_keeps_core_defs_out_of_monolith() -> None:
    function_names = _task_selection_function_names()

    assert "apply_selection_penalty" not in function_names
    assert "select_items_with_batch_diversity" not in function_names
    assert "apply_intra_selection_penalty" not in function_names
    assert "selection_penalty_for_item" not in function_names
    assert "fallback_family_for_category" not in function_names


def test_task_selection_render_module_exports_match_surface() -> None:
    assert (
        task_selection_render_module.render_loop_plan
        is task_selection_module.render_loop_plan
    )
    assert (
        task_selection_render_module.selected_task_action_hint
        is task_selection_module.selected_task_action_hint
    )
    assert (
        task_selection_render_module.selected_task_validation_command
        is task_selection_module.selected_task_validation_command
    )


def test_task_selection_module_keeps_render_defs_out_of_monolith() -> None:
    function_names = _task_selection_function_names()

    assert "render_loop_plan" not in function_names
    assert "selected_task_action_hint" not in function_names
    assert "selected_task_validation_command" not in function_names
    assert "compact_backlog_evidence_summary" not in function_names
