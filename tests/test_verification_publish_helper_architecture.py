"""Architecture tests for internal verification-publish helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.reporters.verification_publish as verification_publish_module
import qa_z.reporters.verification_publish_summary as publish_summary_module
import qa_z.reporters.verification_publish_support as publish_support_module


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


def test_verification_publish_module_keeps_summary_defs_out_of_monolith() -> None:
    function_names = _verification_publish_function_names()

    assert "recommendation_for_verdict" not in function_names
    assert "build_session_verification_publish_summary" not in function_names
    assert "verification_publish_summary_from_session" not in function_names
    assert "failed_verification_publish_summary" not in function_names


def test_verification_publish_module_keeps_support_defs_out_of_monolith() -> None:
    function_names = _verification_publish_function_names()

    assert "action_needed_for" not in function_names
    assert "render_key_artifacts" not in function_names
    assert "read_json_object" not in function_names
    assert "session_summary_path_from_manifest" not in function_names
    assert "resolve_session_dir" not in function_names
    assert "containing_session_dir" not in function_names
    assert "run_id_from_compare" not in function_names
    assert "path_from_manifest" not in function_names
    assert "path_from_nested_manifest" not in function_names
    assert "mapping_value" not in function_names
    assert "int_value" not in function_names
    assert "first_text" not in function_names
    assert "path_name" not in function_names
    assert "string_list" not in function_names
    assert "recommended_action_list" not in function_names
    assert "recommended_action_summary_text" not in function_names


def test_verification_publish_summary_module_exposes_helpers() -> None:
    assert callable(publish_summary_module.recommendation_for_verdict)
    assert callable(publish_summary_module.build_session_verification_publish_summary)
    assert callable(publish_summary_module.verification_publish_summary_from_session)


def test_verification_publish_support_module_exposes_helpers() -> None:
    assert callable(publish_support_module.action_needed_for)
    assert callable(publish_support_module.render_key_artifacts)
    assert callable(publish_support_module.read_json_object)
