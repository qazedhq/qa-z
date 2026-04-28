"""Architecture tests for executor-ingest seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_ingest_candidate as executor_ingest_candidate_module
import qa_z.executor_ingest as executor_ingest_module
import qa_z.executor_ingest_render as executor_ingest_render_module
import qa_z.executor_ingest_runtime as executor_ingest_runtime_module


def _executor_ingest_function_names() -> set[str]:
    source = Path(executor_ingest_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(executor_ingest_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_executor_ingest_runtime_module_exports_match_surface() -> None:
    assert (
        executor_ingest_runtime_module.ingest_executor_result_artifact
        is executor_ingest_module.ingest_executor_result_artifact
    )
    assert (
        executor_ingest_runtime_module.verify_repair_session
        is executor_ingest_module.verify_repair_session
    )
    assert (
        executor_ingest_runtime_module.create_verify_candidate_run
        is executor_ingest_module.create_verify_candidate_run
    )
    assert (
        executor_ingest_runtime_module.write_verify_rerun_review_artifacts
        is executor_ingest_module.write_verify_rerun_review_artifacts
    )
    assert (
        executor_ingest_runtime_module.resolve_fast_selection_mode
        is executor_ingest_module.resolve_fast_selection_mode
    )
    assert (
        executor_ingest_runtime_module.resolve_deep_selection_mode
        is executor_ingest_module.resolve_deep_selection_mode
    )


def test_executor_ingest_runtime_module_reuses_candidate_helpers() -> None:
    assert (
        executor_ingest_runtime_module.create_verify_candidate_run
        is executor_ingest_candidate_module.create_verify_candidate_run
    )
    assert (
        executor_ingest_runtime_module.write_verify_rerun_review_artifacts
        is executor_ingest_candidate_module.write_verify_rerun_review_artifacts
    )
    assert (
        executor_ingest_runtime_module.resolve_fast_selection_mode
        is executor_ingest_candidate_module.resolve_fast_selection_mode
    )
    assert (
        executor_ingest_runtime_module.resolve_deep_selection_mode
        is executor_ingest_candidate_module.resolve_deep_selection_mode
    )


def test_executor_ingest_render_module_exports_match_surface() -> None:
    assert (
        executor_ingest_render_module.render_executor_result_ingest_stdout
        is executor_ingest_module.render_executor_result_ingest_stdout
    )
    assert (
        executor_ingest_render_module.render_ingest_report
        is executor_ingest_module.render_ingest_report
    )


def test_executor_ingest_module_keeps_public_defs_out_of_monolith() -> None:
    function_names = _executor_ingest_function_names()

    assert "ingest_executor_result_artifact" not in function_names
    assert "verify_repair_session" not in function_names
    assert "create_verify_candidate_run" not in function_names
    assert "write_verify_rerun_review_artifacts" not in function_names
    assert "_create_verify_candidate_run_impl" not in function_names
    assert "_write_verify_rerun_review_artifacts_impl" not in function_names
    assert "resolve_fast_selection_mode" not in function_names
    assert "resolve_deep_selection_mode" not in function_names
    assert "render_executor_result_ingest_stdout" not in function_names
    assert "render_ingest_report" not in function_names
    assert "_render_executor_result_ingest_stdout_impl" not in function_names
    assert "_render_ingest_report_impl" not in function_names


def test_executor_ingest_module_uses_explicit_imports() -> None:
    source = Path(executor_ingest_module.__file__).read_text(encoding="utf-8")

    assert "import importlib" not in source
    assert "importlib.import_module" not in source
