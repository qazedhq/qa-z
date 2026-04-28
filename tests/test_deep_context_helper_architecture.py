"""Architecture tests for internal deep-context helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.reporters.deep_context as deep_context_module
import qa_z.reporters.deep_context_findings as deep_context_findings_module
import qa_z.reporters.deep_context_summary as deep_context_summary_module


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


def test_deep_context_module_keeps_findings_defs_out_of_monolith() -> None:
    function_names = _deep_context_function_names()

    assert "normalize_finding" not in function_names
    assert "normalize_grouped_finding" not in function_names
    assert "coerce_count" not in function_names
    assert "unique_preserve_order" not in function_names


def test_deep_context_module_keeps_summary_defs_out_of_monolith() -> None:
    function_names = _deep_context_function_names()

    assert "aggregate_severities" not in function_names
    assert "aggregate_filter_reasons" not in function_names
    assert "infer_blocking_count" not in function_names
    assert "primary_policy" not in function_names
    assert "highest_severity" not in function_names
    assert "severity_sort_key" not in function_names


def test_deep_context_findings_module_exposes_helpers() -> None:
    assert callable(deep_context_findings_module.normalize_finding)
    assert callable(deep_context_findings_module.normalize_grouped_finding)
    assert callable(deep_context_findings_module.unique_preserve_order)


def test_deep_context_summary_module_exposes_helpers() -> None:
    assert callable(deep_context_summary_module.aggregate_severities)
    assert callable(deep_context_summary_module.aggregate_filter_reasons)
    assert callable(deep_context_summary_module.highest_severity)
