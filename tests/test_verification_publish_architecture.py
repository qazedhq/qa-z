"""Architecture tests for verification-publish seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.reporters.verification_publish as verification_publish_module
import qa_z.reporters.verification_publish_loading as verification_publish_loading_module
import qa_z.reporters.verification_publish_render as verification_publish_render_module


def _verification_publish_function_names() -> set[str]:
    source = Path(verification_publish_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(verification_publish_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_verification_publish_loading_module_exports_match_surface() -> None:
    assert (
        verification_publish_loading_module.detect_publish_summary_for_run
        is verification_publish_module.detect_publish_summary_for_run
    )
    assert (
        verification_publish_loading_module.build_verification_publish_summary
        is verification_publish_module.build_verification_publish_summary
    )
    assert (
        verification_publish_loading_module.load_session_publish_summary
        is verification_publish_module.load_session_publish_summary
    )


def test_verification_publish_render_module_exports_match_surface() -> None:
    assert (
        verification_publish_render_module.render_publish_summary_markdown
        is verification_publish_module.render_publish_summary_markdown
    )
    assert (
        verification_publish_render_module.publish_headline
        is verification_publish_module.publish_headline
    )


def test_verification_publish_module_keeps_loading_and_render_defs_out_of_monolith() -> (
    None
):
    function_names = _verification_publish_function_names()

    assert "detect_publish_summary_for_run" not in function_names
    assert "build_verification_publish_summary" not in function_names
    assert "load_session_publish_summary" not in function_names
    assert "render_publish_summary_markdown" not in function_names
    assert "publish_headline" not in function_names


def test_verification_publish_surface_avoids_importlib_facades() -> None:
    source = Path("src/qa_z/reporters/verification_publish.py").read_text(
        encoding="utf-8"
    )

    assert "importlib.import_module" not in source


def test_verification_publish_regression_packs_stay_split() -> None:
    summary_lines = len(
        Path("tests/test_verification_publish_summary.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    session_lines = len(
        Path("tests/test_verification_publish_session.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert summary_lines <= 260, (
        f"test_verification_publish_summary.py exceeded budget: {summary_lines}"
    )
    assert session_lines <= 340, (
        f"test_verification_publish_session.py exceeded budget: {session_lines}"
    )
