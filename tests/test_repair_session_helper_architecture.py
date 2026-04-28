"""Architecture tests for internal repair-session helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.repair_session as repair_session_module
import qa_z.repair_session_dry_run as repair_session_dry_run_module
import qa_z.repair_session_outcome as repair_session_outcome_module


def _repair_session_function_names() -> set[str]:
    source = Path(repair_session_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(repair_session_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_repair_session_module_keeps_dry_run_defs_out_of_monolith() -> None:
    function_names = _repair_session_function_names()

    assert "load_session_dry_run_summary" not in function_names
    assert "synthesize_session_dry_run_summary" not in function_names
    assert "safety_package_id_for_session" not in function_names
    assert "enrich_dry_run_operator_fields" not in function_names
    assert "normalized_dry_run_actions" not in function_names
    assert "dry_run_action_summary_text" not in function_names


def test_repair_session_module_keeps_outcome_defs_out_of_monolith() -> None:
    function_names = _repair_session_function_names()

    assert "session_status_dict" not in function_names
    assert "session_summary_json" not in function_names
    assert "session_summary_dict" not in function_names
    assert "render_outcome_markdown" not in function_names
    assert "recommendation_for_verdict" not in function_names


def test_repair_session_dry_run_module_exposes_helpers() -> None:
    assert callable(repair_session_dry_run_module.load_session_dry_run_summary)
    assert callable(repair_session_dry_run_module.enrich_dry_run_operator_fields)
    assert callable(repair_session_dry_run_module.normalized_dry_run_actions)


def test_repair_session_outcome_module_exposes_helpers() -> None:
    assert callable(repair_session_outcome_module.session_status_dict)
    assert callable(repair_session_outcome_module.session_summary_dict)
    assert callable(repair_session_outcome_module.render_outcome_markdown)
