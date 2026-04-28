"""Architecture tests for repair-session seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.repair_session as repair_session_module
import qa_z.repair_session_lifecycle as repair_session_lifecycle_module
import qa_z.repair_session_render as repair_session_render_module
import qa_z.repair_session_support as repair_session_support_module


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


def test_repair_session_lifecycle_module_exports_match_surface() -> None:
    assert (
        repair_session_lifecycle_module.create_repair_session
        is repair_session_module.create_repair_session
    )
    assert (
        repair_session_lifecycle_module.complete_session_verification
        is repair_session_module.complete_session_verification
    )
    assert (
        repair_session_lifecycle_module.load_repair_session
        is repair_session_module.load_repair_session
    )


def test_repair_session_render_module_exports_match_surface() -> None:
    assert (
        repair_session_render_module.render_session_status
        is repair_session_module.render_session_status
    )
    assert (
        repair_session_render_module.render_session_status_with_dry_run
        is repair_session_module.render_session_status_with_dry_run
    )
    assert (
        repair_session_render_module.render_session_verify_stdout
        is repair_session_module.render_session_verify_stdout
    )
    assert (
        repair_session_render_module.render_session_start_stdout
        is repair_session_module.render_session_start_stdout
    )


def test_repair_session_support_module_exports_match_surface() -> None:
    assert (
        repair_session_support_module.write_session_manifest
        is repair_session_module.write_session_manifest
    )
    assert (
        repair_session_support_module.ensure_session_safety_artifacts
        is repair_session_module.ensure_session_safety_artifacts
    )
    assert (
        repair_session_support_module.resolve_session_dir
        is repair_session_module.resolve_session_dir
    )
    assert (
        repair_session_support_module.sessions_dir is repair_session_module.sessions_dir
    )
    assert (
        repair_session_support_module.create_session_id
        is repair_session_module.create_session_id
    )
    assert (
        repair_session_support_module.normalize_session_id
        is repair_session_module.normalize_session_id
    )


def test_repair_session_module_keeps_lifecycle_and_render_defs_out_of_monolith() -> (
    None
):
    function_names = _repair_session_function_names()

    assert "create_repair_session" not in function_names
    assert "complete_session_verification" not in function_names
    assert "load_repair_session" not in function_names
    assert "render_session_status" not in function_names
    assert "render_session_status_with_dry_run" not in function_names
    assert "render_session_start_stdout" not in function_names
    assert "render_session_verify_stdout" not in function_names
    assert "_render_session_status_impl" not in function_names
    assert "_render_session_status_with_dry_run_impl" not in function_names
    assert "_render_session_verify_stdout_impl" not in function_names
    assert "write_session_manifest" not in function_names
    assert "ensure_session_safety_artifacts" not in function_names
    assert "resolve_session_dir" not in function_names
    assert "sessions_dir" not in function_names
    assert "create_session_id" not in function_names
    assert "normalize_session_id" not in function_names
    assert "utc_now" not in function_names
    assert "optional_string" not in function_names
    assert "string_mapping" not in function_names
    assert "handoff_artifact_paths" not in function_names


def test_repair_session_module_uses_explicit_imports() -> None:
    source = Path(repair_session_module.__file__).read_text(encoding="utf-8")

    assert "import importlib" not in source
    assert "importlib.import_module" not in source
