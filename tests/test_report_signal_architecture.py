"""Architecture tests for report signal seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.docs_drift_signals as docs_drift_signals_module
import qa_z.report_matching as report_matching_module
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


def test_report_matching_module_exports_match_report_surface() -> None:
    assert (
        report_matching_module.matching_report_evidence
        is report_signals_module.matching_report_evidence
    )
    assert (
        report_matching_module.report_documents
        is report_signals_module.report_documents
    )


def test_docs_drift_signals_module_exports_match_report_surface() -> None:
    assert (
        docs_drift_signals_module.discover_docs_drift_candidate_inputs
        is report_signals_module.discover_docs_drift_candidate_inputs
    )


def test_report_signals_module_keeps_docs_matching_defs_out_of_signal_module() -> None:
    function_names = _report_signals_function_names()

    assert "discover_docs_drift_candidate_inputs" not in function_names
    assert "docs_drift_report_evidence" not in function_names
    assert "matching_report_evidence" not in function_names
    assert "report_documents" not in function_names
