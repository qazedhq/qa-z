"""Architecture tests for deep-context seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.reporters.deep_context as deep_context_module
import qa_z.reporters.deep_context_formatting as deep_context_formatting_module
import qa_z.reporters.deep_context_loading as deep_context_loading_module


def _deep_context_function_names() -> set[str]:
    source = Path(deep_context_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(deep_context_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_deep_context_loading_module_exports_match_surface() -> None:
    assert (
        deep_context_loading_module.load_sibling_deep_summary
        is deep_context_module.load_sibling_deep_summary
    )
    assert (
        deep_context_loading_module.build_deep_context
        is deep_context_module.build_deep_context
    )


def test_deep_context_formatting_module_exports_match_surface() -> None:
    assert (
        deep_context_formatting_module.format_severity_summary
        is deep_context_module.format_severity_summary
    )
    assert (
        deep_context_formatting_module.format_finding_location
        is deep_context_module.format_finding_location
    )


def test_deep_context_module_keeps_public_defs_out_of_monolith() -> None:
    function_names = _deep_context_function_names()

    assert "load_sibling_deep_summary" not in function_names
    assert "build_deep_context" not in function_names
    assert "format_severity_summary" not in function_names
    assert "format_finding_location" not in function_names


def test_deep_context_surface_avoids_importlib_facades() -> None:
    source = Path("src/qa_z/reporters/deep_context.py").read_text(encoding="utf-8")

    assert "importlib.import_module" not in source
