"""Architecture tests for GitHub summary seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.reporters.github_summary as github_summary_module
import qa_z.reporters.github_summary_render as github_summary_render_module
import qa_z.reporters.github_summary_sections as github_summary_sections_module


def _github_summary_function_names() -> set[str]:
    source = Path(github_summary_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(github_summary_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_github_summary_render_module_exports_match_surface() -> None:
    assert (
        github_summary_render_module.render_github_summary
        is github_summary_module.render_github_summary
    )


def test_github_summary_module_keeps_render_and_section_defs_out_of_monolith() -> None:
    function_names = _github_summary_function_names()

    assert "render_github_summary" not in function_names
    assert "render_failed_check" not in function_names
    assert "render_changed_files" not in function_names
    assert "render_selection" not in function_names
    assert "format_code_list" not in function_names
    assert "render_deep_qa" not in function_names
    assert "format_grouped_finding" not in function_names
    assert "coerce_count" not in function_names


def test_github_summary_sections_module_exposes_section_helpers() -> None:
    assert callable(github_summary_sections_module.render_failed_check)
    assert callable(github_summary_sections_module.render_changed_files)
    assert callable(github_summary_sections_module.render_selection)
    assert callable(github_summary_sections_module.render_deep_qa)


def test_github_summary_surface_avoids_importlib_facades() -> None:
    source = Path("src/qa_z/reporters/github_summary.py").read_text(encoding="utf-8")

    assert "importlib.import_module" not in source


def test_github_summary_regression_packs_stay_split() -> None:
    render_lines = len(
        Path("tests/test_github_summary_render.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    session_lines = len(
        Path("tests/test_github_summary_session.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    deep_lines = len(
        Path("tests/test_github_summary_deep.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert render_lines <= 220, (
        f"test_github_summary_render.py exceeded budget: {render_lines}"
    )
    assert session_lines <= 280, (
        f"test_github_summary_session.py exceeded budget: {session_lines}"
    )
    assert deep_lines <= 180, (
        f"test_github_summary_deep.py exceeded budget: {deep_lines}"
    )
