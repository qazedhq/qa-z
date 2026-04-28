"""Architecture tests for verification finding-compare support seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body


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


def test_verification_findings_module_keeps_compare_support_defs_out_of_core() -> None:
    function_names = _verification_findings_function_names()

    assert "classify_matched_finding" not in function_names
    assert "finding_delta" not in function_names
    assert "_empty_categories" not in function_names
