"""Architecture tests for executor dry-run seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_dry_run as executor_dry_run_module
import qa_z.executor_dry_run_render as executor_dry_run_render_module
import qa_z.executor_dry_run_summary as executor_dry_run_summary_module


def _executor_dry_run_function_names() -> set[str]:
    source = Path(executor_dry_run_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(executor_dry_run_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_executor_dry_run_summary_module_exports_match_surface() -> None:
    assert (
        executor_dry_run_summary_module.load_safety_package
        is executor_dry_run_module.load_safety_package
    )
    assert (
        executor_dry_run_summary_module.dry_run_summary
        is executor_dry_run_module.dry_run_summary
    )


def test_executor_dry_run_render_module_exports_match_surface() -> None:
    assert (
        executor_dry_run_render_module.render_dry_run_report
        is executor_dry_run_module.render_dry_run_report
    )
    assert (
        executor_dry_run_render_module.normalize_recommended_actions
        is executor_dry_run_module.normalize_recommended_actions
    )


def test_executor_dry_run_module_keeps_split_defs_out_of_monolith() -> None:
    function_names = _executor_dry_run_function_names()

    assert "load_safety_package" not in function_names
    assert "dry_run_summary" not in function_names
    assert "render_dry_run_report" not in function_names
    assert "normalize_recommended_actions" not in function_names
