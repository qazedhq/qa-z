"""Architecture tests for report freshness helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.report_freshness as report_freshness_module
import qa_z.report_signals as report_signals_module


def _report_signals_function_names() -> set[str]:
    source = Path(report_signals_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(report_signals_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_report_freshness_module_exports_match_report_surface() -> None:
    assert (
        report_freshness_module.inspection_date is report_signals_module.inspection_date
    )
    assert (
        report_freshness_module.report_document_date
        is report_signals_module.report_document_date
    )
    assert (
        report_freshness_module.report_document_branch
        is report_signals_module.report_document_branch
    )
    assert (
        report_freshness_module.report_document_head
        is report_signals_module.report_document_head
    )
    assert (
        report_freshness_module.report_freshness_summary
        is report_signals_module.report_freshness_summary
    )
    assert (
        report_freshness_module.report_is_stale_for_inspection
        is report_signals_module.report_is_stale_for_inspection
    )


def test_report_signals_module_keeps_freshness_defs_out_of_signal_module() -> None:
    function_names = _report_signals_function_names()

    assert "inspection_date" not in function_names
    assert "report_document_date" not in function_names
    assert "report_document_branch" not in function_names
    assert "report_document_head" not in function_names
    assert "report_freshness_summary" not in function_names
    assert "report_is_stale_for_inspection" not in function_names
