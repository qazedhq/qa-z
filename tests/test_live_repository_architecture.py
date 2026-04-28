"""Architecture tests for live repository seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.live_repository as live_repository_module
import qa_z.live_repository_git as live_repository_git_module
import qa_z.live_repository_render as live_repository_render_module


def _live_repository_function_names() -> set[str]:
    source = Path(live_repository_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(live_repository_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_live_repository_git_module_exports_match_surface() -> None:
    assert (
        live_repository_git_module.git_worktree_snapshot
        is live_repository_module.git_worktree_snapshot
    )
    assert (
        live_repository_git_module.git_current_branch
        is live_repository_module.git_current_branch
    )
    assert (
        live_repository_git_module.git_current_head
        is live_repository_module.git_current_head
    )


def test_live_repository_module_keeps_git_defs_out_of_monolith() -> None:
    function_names = _live_repository_function_names()

    assert "git_worktree_snapshot" not in function_names
    assert "git_current_branch" not in function_names
    assert "git_current_head" not in function_names
    assert "parse_git_status_output" not in function_names
    assert "normalize_git_status_path" not in function_names


def test_live_repository_render_module_exports_match_surface() -> None:
    assert (
        live_repository_render_module.live_repository_summary
        is live_repository_module.live_repository_summary
    )
    assert (
        live_repository_render_module.render_live_repository_summary
        is live_repository_module.render_live_repository_summary
    )
    assert (
        live_repository_render_module.classify_worktree_path_area
        is live_repository_module.classify_worktree_path_area
    )
    assert (
        live_repository_render_module.is_runtime_artifact_path
        is live_repository_module.is_runtime_artifact_path
    )


def test_live_repository_module_keeps_render_defs_out_of_monolith() -> None:
    function_names = _live_repository_function_names()

    assert "live_repository_summary" not in function_names
    assert "render_live_repository_summary" not in function_names
    assert "classify_worktree_path_area" not in function_names
    assert "worktree_area_summary" not in function_names
    assert "is_runtime_artifact_path" not in function_names
