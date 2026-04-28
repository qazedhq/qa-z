"""Architecture tests for modular review command seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.commands.review_github as review_github_module
import qa_z.commands.review_packet as review_packet_module
import qa_z.commands.reviewing as reviewing_module


def _reviewing_function_names() -> set[str]:
    source = Path(reviewing_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(reviewing_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_review_packet_module_exports_match_reviewing_surface() -> None:
    assert review_packet_module.handle_review is reviewing_module.handle_review
    assert (
        review_packet_module.register_review_command
        is reviewing_module.register_review_command
    )


def test_reviewing_module_keeps_review_defs_out_of_monolith() -> None:
    function_names = _reviewing_function_names()

    assert "handle_review" not in function_names
    assert "register_review_command" not in function_names


def test_review_github_module_exports_match_reviewing_surface() -> None:
    assert (
        review_github_module.handle_github_summary
        is reviewing_module.handle_github_summary
    )
    assert (
        review_github_module.register_github_summary_command
        is reviewing_module.register_github_summary_command
    )


def test_reviewing_module_keeps_github_defs_out_of_monolith() -> None:
    function_names = _reviewing_function_names()

    assert "handle_github_summary" not in function_names
    assert "register_github_summary_command" not in function_names
