"""Architecture tests for executor-bridge seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_bridge as executor_bridge_module
import qa_z.executor_bridge_loop as executor_bridge_loop_module
import qa_z.executor_bridge_package as executor_bridge_package_module
import qa_z.executor_bridge_render as executor_bridge_render_module
import qa_z.executor_bridge_context as executor_bridge_context_module
import qa_z.executor_bridge_support as executor_bridge_support_module


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


def test_executor_bridge_package_module_exports_match_surface() -> None:
    assert (
        executor_bridge_package_module.create_executor_bridge
        is executor_bridge_module.create_executor_bridge
    )
    assert (
        executor_bridge_package_module.bridge_manifest
        is executor_bridge_module.bridge_manifest
    )
    assert callable(executor_bridge_package_module.copy_bridge_inputs)
    assert callable(executor_bridge_package_module.bridge_validation_commands)
    assert callable(executor_bridge_package_module.bridge_live_repository_context)


def test_executor_bridge_render_module_exports_match_surface() -> None:
    assert (
        executor_bridge_render_module.render_executor_bridge_guide
        is executor_bridge_module.render_executor_bridge_guide
    )
    assert (
        executor_bridge_render_module.render_bridge_stdout
        is executor_bridge_module.render_bridge_stdout
    )


def test_executor_bridge_loop_module_exports_match_surface() -> None:
    assert (
        executor_bridge_loop_module.load_loop_outcome
        is executor_bridge_module.load_loop_outcome
    )
    assert (
        executor_bridge_loop_module.resolve_loop_outcome_path
        is executor_bridge_module.resolve_loop_outcome_path
    )
    assert (
        executor_bridge_loop_module.repair_session_action
        is executor_bridge_module.repair_session_action
    )
    assert (
        executor_bridge_loop_module.read_json_object
        is executor_bridge_module.read_json_object
    )


def test_executor_bridge_support_module_exports_match_surface() -> None:
    assert (
        executor_bridge_support_module.write_json is executor_bridge_module.write_json
    )
    assert (
        executor_bridge_support_module.normalize_bridge_id
        is executor_bridge_module.normalize_bridge_id
    )
    assert (
        executor_bridge_support_module.default_bridge_id
        is executor_bridge_module.default_bridge_id
    )
    assert executor_bridge_support_module.slugify is executor_bridge_module.slugify
    assert (
        executor_bridge_support_module.format_command
        is executor_bridge_module.format_command
    )
    assert (
        executor_bridge_support_module.resolve_bridge_dir
        is executor_bridge_module.resolve_bridge_dir
    )
    assert (
        executor_bridge_support_module.ensure_session_exists
        is executor_bridge_module.ensure_session_exists
    )


def test_executor_bridge_context_module_exports_match_surface() -> None:
    assert (
        executor_bridge_context_module.resolve_path
        is executor_bridge_module.resolve_path
    )
    assert (
        executor_bridge_context_module.path_is_within
        is executor_bridge_module.path_is_within
    )
    assert (
        executor_bridge_context_module.context_source_label
        is executor_bridge_module.context_source_label
    )
    assert (
        executor_bridge_context_module.safe_context_input_name
        is executor_bridge_module.safe_context_input_name
    )
    assert (
        executor_bridge_context_module.bridge_action_context_inputs
        is executor_bridge_module.bridge_action_context_inputs
    )
    assert (
        executor_bridge_context_module.bridge_missing_action_context_inputs
        is executor_bridge_module.bridge_missing_action_context_inputs
    )
    assert callable(executor_bridge_context_module.copy_action_context_inputs)
    assert callable(executor_bridge_context_module.action_context_paths)


def test_executor_bridge_module_keeps_package_and_render_defs_out_of_monolith() -> None:
    function_names = _executor_bridge_function_names()

    assert "create_executor_bridge" not in function_names
    assert "bridge_manifest" not in function_names
    assert "_create_executor_bridge_impl" not in function_names
    assert "_bridge_manifest_impl" not in function_names
    assert "render_executor_bridge_guide" not in function_names
    assert "render_bridge_stdout" not in function_names
    assert "load_loop_outcome" not in function_names
    assert "resolve_loop_outcome_path" not in function_names
    assert "repair_session_action" not in function_names
    assert "read_json_object" not in function_names
    assert "write_json" not in function_names
    assert "normalize_bridge_id" not in function_names
    assert "default_bridge_id" not in function_names
    assert "slugify" not in function_names
    assert "format_command" not in function_names
    assert "resolve_bridge_dir" not in function_names
    assert "ensure_session_exists" not in function_names
    assert "resolve_path" not in function_names
    assert "path_is_within" not in function_names
    assert "context_source_label" not in function_names
    assert "safe_context_input_name" not in function_names
    assert "bridge_action_context_inputs" not in function_names
    assert "bridge_missing_action_context_inputs" not in function_names
    assert "copy_input" not in function_names
    assert "bridge_live_repository_context" not in function_names
    assert "copy_bridge_inputs" not in function_names
    assert "copy_action_context_inputs" not in function_names
    assert "action_context_paths" not in function_names
    assert "bridge_validation_commands" not in function_names


def test_executor_bridge_module_uses_explicit_imports() -> None:
    source = Path(executor_bridge_module.__file__).read_text(encoding="utf-8")

    assert "import importlib" not in source
    assert "importlib.import_module" not in source
