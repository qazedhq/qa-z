"""Architecture tests for verification finding-support seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.verification as verification_module
import qa_z.verification_finding_support as verification_finding_support_module


def _verification_findings_function_names() -> set[str]:
    source = Path("src/qa_z/verification_findings.py").read_text(encoding="utf-8")
    tree = compile(
        source,
        "src/qa_z/verification_findings.py",
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_verification_finding_support_module_exports_match_surface() -> None:
    assert (
        verification_finding_support_module.find_matching_candidate
        is verification_module.find_matching_candidate
    )
    assert (
        verification_finding_support_module.extract_deep_findings
        is verification_module.extract_deep_findings
    )
    assert (
        verification_finding_support_module.normalize_active_finding
        is verification_module.normalize_active_finding
    )
    assert (
        verification_finding_support_module.normalize_grouped_finding
        is verification_module.normalize_grouped_finding
    )
    assert (
        verification_finding_support_module.blocking_severities
        is verification_module.blocking_severities
    )


def test_verification_findings_module_keeps_support_defs_out_of_compare_module() -> (
    None
):
    function_names = _verification_findings_function_names()

    assert "find_matching_candidate" not in function_names
    assert "extract_deep_findings" not in function_names
    assert "normalize_active_finding" not in function_names
    assert "normalize_grouped_finding" not in function_names
    assert "blocking_severities" not in function_names
