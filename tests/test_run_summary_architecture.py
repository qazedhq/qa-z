"""Architecture tests for run-summary seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.reporters.run_summary as run_summary_module
import qa_z.reporters.run_summary_artifacts as run_summary_artifacts_module
import qa_z.reporters.run_summary_render as run_summary_render_module


def _run_summary_function_names() -> set[str]:
    source = Path(run_summary_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(run_summary_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_run_summary_artifacts_module_exports_match_surface() -> None:
    assert (
        run_summary_artifacts_module.write_run_summary_artifacts
        is run_summary_module.write_run_summary_artifacts
    )


def test_run_summary_render_module_exports_match_surface() -> None:
    assert (
        run_summary_render_module.render_summary_markdown
        is run_summary_module.render_summary_markdown
    )


def test_run_summary_module_keeps_artifact_and_render_defs_out_of_monolith() -> None:
    function_names = _run_summary_function_names()

    assert "write_run_summary_artifacts" not in function_names
    assert "render_summary_markdown" not in function_names


def test_run_summary_surface_avoids_importlib_facades() -> None:
    source = Path("src/qa_z/reporters/run_summary.py").read_text(encoding="utf-8")

    assert "importlib.import_module" not in source
