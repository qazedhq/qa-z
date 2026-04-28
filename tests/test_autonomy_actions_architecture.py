from __future__ import annotations

import ast
from pathlib import Path

import qa_z.autonomy_actions as autonomy_actions_module

from tests.ast_test_support import module_body


def test_autonomy_actions_module_keeps_extracted_helper_defs_out_of_orchestrator() -> (
    None
):
    source = Path(autonomy_actions_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(autonomy_actions_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }

    assert "cleanup_action" not in function_names
    assert "workflow_gap_action" not in function_names
    assert "task_context_paths" not in function_names
    assert "recommendation_context_paths" not in function_names
    assert "loop_local_self_inspection_context_paths" not in function_names
    assert "merge_context_paths" not in function_names
    assert "baseline_run_from_verify_evidence" not in function_names
    assert "executor_dry_run_command" not in function_names
    assert "existing_session_id" not in function_names
    assert "resolve_evidence_path" not in function_names
    assert "read_json_object" not in function_names
    assert "repair_session_action" not in function_names
