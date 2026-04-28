"""Architecture tests for internal executor-bridge helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_bridge as executor_bridge_module
import qa_z.executor_bridge_guides as executor_bridge_guides_module
import qa_z.executor_bridge_summary as executor_bridge_summary_module


def _executor_bridge_function_names() -> set[str]:
    source = Path(executor_bridge_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(executor_bridge_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_executor_bridge_module_keeps_summary_defs_out_of_monolith() -> None:
    function_names = _executor_bridge_function_names()

    assert "bridge_evidence_summary" not in function_names
    assert "bridge_safety_package_summary" not in function_names
    assert "bridge_safety_rule_count" not in function_names


def test_executor_bridge_module_keeps_guide_defs_out_of_monolith() -> None:
    function_names = _executor_bridge_function_names()

    assert "bridge_placeholder_summary_guidance" not in function_names
    assert "render_executor_specific_guide" not in function_names


def test_executor_bridge_summary_module_exposes_helpers() -> None:
    assert callable(executor_bridge_summary_module.bridge_evidence_summary)
    assert callable(executor_bridge_summary_module.bridge_safety_package_summary)
    assert callable(executor_bridge_summary_module.bridge_safety_rule_count)


def test_executor_bridge_guides_module_exposes_helpers() -> None:
    assert callable(executor_bridge_guides_module.bridge_placeholder_summary_guidance)
    assert callable(executor_bridge_guides_module.render_executor_specific_guide)
